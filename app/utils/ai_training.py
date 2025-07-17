"""
AI Chatbot Training Utilities
Handles model fine-tuning, training data preparation, and performance monitoring
"""
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import os

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset
import torch

from app.core.settings import get_settings
from app.schemas.ai_advisor import AITrainingData, ModelPerformanceMetrics
from app.db.repositories import ConversationRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatbotTrainer:
    """
    Handles training and fine-tuning of the financial chatbot
    """
    
    def __init__(self):
        self.model_name = "microsoft/DialoGPT-medium"  # Good for conversational AI
        self.tokenizer = None
        self.model = None
        self.training_data_path = Path("data/training")
        self.model_save_path = Path("models/financial_advisor")
        
        # Ensure directories exist
        self.training_data_path.mkdir(parents=True, exist_ok=True)
        self.model_save_path.mkdir(parents=True, exist_ok=True)
    
    async def prepare_training_data(
        self, 
        conversation_data: List[AITrainingData],
        include_financial_context: bool = True
    ) -> Dataset:
        """
        Prepare conversation data for training
        """
        logger.info(f"Preparing {len(conversation_data)} conversations for training")
        
        # Convert to training format
        training_examples = []
        
        for conversation in conversation_data:
            example = {
                "input_text": conversation.user_message,
                "target_text": conversation.ai_response,
                "context": json.dumps(conversation.context) if conversation.context else "",
                "feedback_score": conversation.feedback_score or 3,
                "timestamp": conversation.created_at.isoformat()
            }
            
            # Add financial context if available
            if include_financial_context and conversation.context:
                financial_context = self._extract_financial_context(conversation.context)
                example["financial_context"] = json.dumps(financial_context)
            
            training_examples.append(example)
        
        # Convert to Hugging Face Dataset
        df = pd.DataFrame(training_examples)
        dataset = Dataset.from_pandas(df)
        
        # Save training data for audit
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(self.training_data_path / f"training_data_{timestamp}.csv", index=False)
        
        return dataset
    
    def _extract_financial_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant financial context for training"""
        financial_keys = [
            "spending_amount", "budget_status", "account_balance", 
            "category", "transaction_type", "goal_progress", "debt_amount"
        ]
        
        return {
            key: context.get(key) 
            for key in financial_keys 
            if context.get(key) is not None
        }
    
    async def fine_tune_model(
        self, 
        training_dataset: Dataset,
        validation_split: float = 0.2,
        epochs: int = 3,
        learning_rate: float = 5e-5
    ) -> Dict[str, Any]:
        """
        Fine-tune the conversational model on financial advice data
        """
        logger.info("Starting model fine-tuning")
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=5  # For feedback score classification
            )
            
            # Add special tokens for financial context
            special_tokens = {
                "pad_token": "[PAD]",
                "additional_special_tokens": ["[FINANCIAL_CONTEXT]", "[USER_GOAL]", "[ADVICE]"]
            }
            self.tokenizer.add_special_tokens(special_tokens)
            self.model.resize_token_embeddings(len(self.tokenizer))
            
            # Tokenize dataset
            def tokenize_function(examples):
                # Combine input text with context
                inputs = []
                for i, text in enumerate(examples["input_text"]):
                    context = examples.get("context", [""] * len(examples["input_text"]))[i]
                    if context:
                        combined_input = f"[FINANCIAL_CONTEXT] {context} [USER_GOAL] {text}"
                    else:
                        combined_input = text
                    inputs.append(combined_input)
                
                tokenized = self.tokenizer(
                    inputs,
                    truncation=True,
                    padding=True,
                    max_length=512
                )
                
                # Add labels (feedback scores)
                tokenized["labels"] = [
                    score - 1 for score in examples["feedback_score"]  # Convert to 0-4 range
                ]
                
                return tokenized
            
            tokenized_dataset = training_dataset.map(tokenize_function, batched=True)
            
            # Split into train/validation
            train_dataset = tokenized_dataset.train_test_split(
                test_size=validation_split, 
                seed=42
            )
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.model_save_path),
                num_train_epochs=epochs,
                per_device_train_batch_size=4,  # Small batch for mobile optimization
                per_device_eval_batch_size=4,
                warmup_steps=500,
                weight_decay=0.01,
                learning_rate=learning_rate,
                logging_dir=str(self.model_save_path / "logs"),
                logging_steps=10,
                evaluation_strategy="steps",
                eval_steps=500,
                save_steps=1000,
                save_total_limit=2,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                fp16=True,  # Mixed precision for efficiency
            )
            
            # Data collator
            data_collator = DataCollatorWithPadding(self.tokenizer)
            
            # Trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset["train"],
                eval_dataset=train_dataset["test"],
                tokenizer=self.tokenizer,
                data_collator=data_collator,
                compute_metrics=self._compute_metrics,
            )
            
            # Train the model
            training_result = trainer.train()
            
            # Save the model
            trainer.save_model()
            self.tokenizer.save_pretrained(str(self.model_save_path))
            
            # Evaluate the model
            eval_results = trainer.evaluate()
            
            return {
                "training_loss": training_result.training_loss,
                "eval_loss": eval_results["eval_loss"],
                "eval_accuracy": eval_results.get("eval_accuracy", 0),
                "training_time": training_result.metrics.get("train_runtime", 0),
                "model_path": str(self.model_save_path)
            }
            
        except Exception as e:
            logger.error(f"Error during model fine-tuning: {str(e)}")
            raise
    
    def _compute_metrics(self, eval_pred):
        """Compute metrics for evaluation"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='weighted'
        )
        accuracy = accuracy_score(labels, predictions)
        
        return {
            'accuracy': accuracy,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
    
    async def evaluate_model_performance(
        self, 
        test_conversations: List[AITrainingData]
    ) -> ModelPerformanceMetrics:
        """
        Evaluate model performance on test data
        """
        if not self.model or not self.tokenizer:
            raise ValueError("Model not loaded. Train or load a model first.")
        
        start_time = datetime.now()
        
        # Prepare test data
        test_inputs = []
        true_scores = []
        
        for conversation in test_conversations:
            test_inputs.append(conversation.user_message)
            true_scores.append(conversation.feedback_score or 3)
        
        # Get model predictions
        predicted_scores = []
        total_response_time = 0
        
        for input_text in test_inputs:
            response_start = datetime.now()
            
            # Tokenize and predict
            inputs = self.tokenizer(
                input_text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True,
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predicted_class = torch.argmax(outputs.logits, dim=1).item()
                predicted_scores.append(predicted_class + 1)  # Convert back to 1-5 range
            
            response_time = (datetime.now() - response_start).total_seconds() * 1000
            total_response_time += response_time
        
        # Calculate metrics
        accuracy = accuracy_score(true_scores, predicted_scores)
        avg_response_time = total_response_time / len(test_inputs) if test_inputs else 0
        
        # Calculate user satisfaction (based on feedback scores)
        satisfaction_scores = [score for score in true_scores if score is not None]
        avg_satisfaction = np.mean(satisfaction_scores) if satisfaction_scores else 3.0
        
        return ModelPerformanceMetrics(
            accuracy_score=accuracy,
            user_satisfaction=avg_satisfaction,
            response_time_ms=int(avg_response_time),
            context_relevance=0.85,  # This would be calculated based on context matching
            advice_effectiveness=None,  # Would require long-term tracking
            timestamp=datetime.utcnow()
        )
    
    async def load_pretrained_model(self, model_path: Optional[str] = None):
        """Load a pre-trained model"""
        path = model_path or str(self.model_save_path)
        
        if not Path(path).exists():
            logger.warning(f"Model path {path} does not exist. Using base model.")
            path = self.model_name
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(path)
            self.model = AutoModelForSequenceClassification.from_pretrained(path)
            logger.info(f"Loaded model from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    async def generate_synthetic_training_data(
        self, 
        num_examples: int = 100
    ) -> List[AITrainingData]:
        """
        Generate synthetic training data for common financial scenarios
        """
        synthetic_data = []
        
        # Common financial conversation patterns
        patterns = [
            {
                "user_message": "I'm spending too much on dining out",
                "ai_response": "I understand your concern about dining expenses. Let's create a realistic dining budget and explore meal prep strategies to help you save money while still enjoying good food.",
                "context": {"category": "dining", "spending_amount": 450},
                "feedback_score": 4
            },
            {
                "user_message": "How can I start saving for an emergency fund?",
                "ai_response": "Great question! Start by saving just $25-50 per paycheck. Set up automatic transfers to a separate savings account. Aim for $1,000 first, then work toward 3-6 months of expenses.",
                "context": {"goal_type": "emergency_fund", "current_savings": 0},
                "feedback_score": 5
            },
            {
                "user_message": "I feel overwhelmed by my debt",
                "ai_response": "I hear you - debt can feel overwhelming, but you're taking the right step by addressing it. Let's list all your debts and create a manageable payoff plan. You've got this! 💪",
                "context": {"debt_amount": 15000, "emotional_state": "overwhelmed"},
                "feedback_score": 4
            }
        ]
        
        # Generate variations of these patterns
        for i in range(num_examples):
            base_pattern = patterns[i % len(patterns)]
            
            # Add some variation
            synthetic_example = AITrainingData(
                user_message=base_pattern["user_message"],
                ai_response=base_pattern["ai_response"],
                context=base_pattern["context"],
                feedback_score=base_pattern["feedback_score"],
                created_at=datetime.utcnow() - timedelta(days=np.random.randint(1, 365))
            )
            
            synthetic_data.append(synthetic_example)
        
        return synthetic_data
    
    async def incremental_learning(
        self, 
        new_conversations: List[AITrainingData],
        learning_rate: float = 1e-5
    ):
        """
        Perform incremental learning with new conversation data
        """
        logger.info(f"Starting incremental learning with {len(new_conversations)} new conversations")
        
        if not self.model:
            await self.load_pretrained_model()
        
        # Prepare new data
        new_dataset = await self.prepare_training_data(new_conversations)
        
        # Fine-tune with lower learning rate
        result = await self.fine_tune_model(
            new_dataset,
            epochs=1,  # Single epoch for incremental learning
            learning_rate=learning_rate
        )
        
        logger.info("Incremental learning completed")
        return result


class ConversationAnalyzer:
    """
    Analyzes conversation patterns for training insights
    """
    
    def __init__(self):
        self.conversation_repo = ConversationRepository()
    
    async def analyze_conversation_patterns(
        self, 
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze conversation patterns to improve training
        """
        # Get recent conversations
        start_date = datetime.utcnow() - timedelta(days=days_back)
        conversations = await self.conversation_repo.get_conversations_since(start_date)
        
        if not conversations:
            return {"status": "no_data"}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([
            {
                "user_message": conv.user_message,
                "ai_response": conv.ai_response,
                "feedback_score": conv.feedback_score,
                "context": conv.context,
                "timestamp": conv.created_at
            }
            for conv in conversations
        ])
        
        analysis = {
            "total_conversations": len(df),
            "avg_feedback_score": df["feedback_score"].mean(),
            "low_score_conversations": len(df[df["feedback_score"] <= 2]),
            "high_score_conversations": len(df[df["feedback_score"] >= 4]),
            "common_topics": self._extract_common_topics(df),
            "improvement_areas": self._identify_improvement_areas(df),
            "training_recommendations": self._generate_training_recommendations(df)
        }
        
        return analysis
    
    def _extract_common_topics(self, df: pd.DataFrame) -> List[str]:
        """Extract common conversation topics"""
        # Simple keyword extraction (could be enhanced with NLP)
        keywords = ["budget", "saving", "debt", "spending", "investment", "emergency fund"]
        topic_counts = {}
        
        for keyword in keywords:
            count = df["user_message"].str.contains(keyword, case=False).sum()
            if count > 0:
                topic_counts[keyword] = count
        
        # Return top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:5]]
    
    def _identify_improvement_areas(self, df: pd.DataFrame) -> List[str]:
        """Identify areas where the model needs improvement"""
        improvements = []
        
        # Low feedback score conversations
        low_score_df = df[df["feedback_score"] <= 2]
        if len(low_score_df) > 0:
            improvements.append("Response quality for complex questions")
        
        # Response length analysis
        df["response_length"] = df["ai_response"].str.len()
        if df["response_length"].mean() > 500:
            improvements.append("Response conciseness for mobile users")
        
        return improvements
    
    def _generate_training_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate recommendations for improving training"""
        recommendations = []
        
        avg_score = df["feedback_score"].mean()
        
        if avg_score < 3.5:
            recommendations.append("Increase training data quality and diversity")
        
        if len(df[df["feedback_score"] <= 2]) > len(df) * 0.2:
            recommendations.append("Focus on improving responses for complex financial scenarios")
        
        recommendations.append("Regular incremental learning with new conversation data")
        
        return recommendations
