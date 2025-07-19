#!/usr/bin/env python3
"""
AI 모델 관리 플랫폼 (MLOps)
"""
import os
import json
import pickle
import shutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path
import hashlib
from enum import Enum
import asyncio
import aiofiles

# 모델 관리
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from mlflow.tracking import MlflowClient

# 모니터링
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, mean_squared_error, f1_score
import psutil
import GPUtil

# 버전 관리
import git
from packaging import version

# 스케줄링
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 알림
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """모델 상태"""
    TRAINING = "training"
    VALIDATING = "validating"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelType(Enum):
    """모델 유형"""
    TIME_SERIES = "time_series"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NLP = "nlp"
    RECOMMENDATION = "recommendation"
    ANOMALY_DETECTION = "anomaly_detection"


class ModelMetrics:
    """모델 메트릭"""
    
    def __init__(self):
        self.metrics_history = []
        
    def add_metrics(self, metrics: Dict[str, float], timestamp: Optional[datetime] = None):
        """메트릭 추가"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.metrics_history.append({
            'timestamp': timestamp,
            'metrics': metrics
        })
        
    def get_latest_metrics(self) -> Dict[str, float]:
        """최신 메트릭 반환"""
        if not self.metrics_history:
            return {}
        return self.metrics_history[-1]['metrics']
        
    def get_metrics_trend(self, metric_name: str, days: int = 7) -> List[Tuple[datetime, float]]:
        """메트릭 추세 반환"""
        cutoff = datetime.now() - timedelta(days=days)
        trend = []
        
        for entry in self.metrics_history:
            if entry['timestamp'] >= cutoff and metric_name in entry['metrics']:
                trend.append((entry['timestamp'], entry['metrics'][metric_name]))
                
        return trend


class ModelVersion:
    """모델 버전 관리"""
    
    def __init__(self, model_id: str, version: str, model_path: str,
                 metadata: Dict[str, Any]):
        self.model_id = model_id
        self.version = version
        self.model_path = model_path
        self.metadata = metadata
        self.created_at = datetime.now()
        self.status = ModelStatus.STAGING
        self.metrics = ModelMetrics()
        self.deployment_history = []
        
    def promote_to_production(self):
        """프로덕션으로 승격"""
        self.status = ModelStatus.PRODUCTION
        self.deployment_history.append({
            'action': 'promoted_to_production',
            'timestamp': datetime.now()
        })
        
    def archive(self):
        """아카이브"""
        self.status = ModelStatus.ARCHIVED
        self.deployment_history.append({
            'action': 'archived',
            'timestamp': datetime.now()
        })


class ModelRegistry:
    """모델 레지스트리"""
    
    def __init__(self, registry_path: str = "./model_registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(exist_ok=True)
        self.models: Dict[str, Dict[str, ModelVersion]] = {}
        self._load_registry()
        
    def _load_registry(self):
        """레지스트리 로드"""
        registry_file = self.registry_path / "registry.json"
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                registry_data = json.load(f)
                # 모델 버전 복원
                for model_id, versions in registry_data.items():
                    self.models[model_id] = {}
                    for version_str, version_data in versions.items():
                        model_version = ModelVersion(
                            model_id=model_id,
                            version=version_str,
                            model_path=version_data['model_path'],
                            metadata=version_data['metadata']
                        )
                        model_version.status = ModelStatus(version_data['status'])
                        model_version.created_at = datetime.fromisoformat(version_data['created_at'])
                        self.models[model_id][version_str] = model_version
                        
    def _save_registry(self):
        """레지스트리 저장"""
        registry_data = {}
        for model_id, versions in self.models.items():
            registry_data[model_id] = {}
            for version_str, model_version in versions.items():
                registry_data[model_id][version_str] = {
                    'model_path': model_version.model_path,
                    'metadata': model_version.metadata,
                    'status': model_version.status.value,
                    'created_at': model_version.created_at.isoformat()
                }
                
        registry_file = self.registry_path / "registry.json"
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)
            
    def register_model(self, model_id: str, version: str, model_path: str,
                      metadata: Dict[str, Any]) -> ModelVersion:
        """모델 등록"""
        if model_id not in self.models:
            self.models[model_id] = {}
            
        # 버전 중복 확인
        if version in self.models[model_id]:
            raise ValueError(f"Model {model_id} version {version} already exists")
            
        # 모델 파일 복사
        model_dir = self.registry_path / model_id / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = model_dir / Path(model_path).name
        shutil.copy2(model_path, dest_path)
        
        # 모델 버전 생성
        model_version = ModelVersion(
            model_id=model_id,
            version=version,
            model_path=str(dest_path),
            metadata=metadata
        )
        
        self.models[model_id][version] = model_version
        self._save_registry()
        
        logger.info(f"Model {model_id} version {version} registered")
        return model_version
        
    def get_model(self, model_id: str, version: Optional[str] = None) -> ModelVersion:
        """모델 조회"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
            
        if version is None:
            # 최신 프로덕션 버전 반환
            prod_versions = [
                (v, mv) for v, mv in self.models[model_id].items()
                if mv.status == ModelStatus.PRODUCTION
            ]
            if not prod_versions:
                # 프로덕션 버전이 없으면 최신 버전 반환
                versions = sorted(self.models[model_id].keys(), 
                                key=lambda x: version.parse(x), reverse=True)
                version = versions[0]
            else:
                version = sorted(prod_versions, key=lambda x: version.parse(x[0]), 
                               reverse=True)[0][0]
                               
        if version not in self.models[model_id]:
            raise ValueError(f"Model {model_id} version {version} not found")
            
        return self.models[model_id][version]
        
    def list_models(self) -> List[Dict[str, Any]]:
        """모델 목록"""
        models_list = []
        for model_id, versions in self.models.items():
            for version_str, model_version in versions.items():
                models_list.append({
                    'model_id': model_id,
                    'version': version_str,
                    'status': model_version.status.value,
                    'created_at': model_version.created_at,
                    'metadata': model_version.metadata
                })
        return models_list


class ModelMonitor:
    """모델 모니터링"""
    
    def __init__(self):
        self.monitoring_data = {}
        self.alert_thresholds = {
            'accuracy_drop': 0.1,  # 10% 정확도 하락
            'latency_increase': 2.0,  # 2배 지연 증가
            'error_rate': 0.05,  # 5% 오류율
            'memory_usage': 0.9  # 90% 메모리 사용
        }
        self.alert_callbacks = []
        
    def add_alert_callback(self, callback):
        """알림 콜백 추가"""
        self.alert_callbacks.append(callback)
        
    async def monitor_performance(self, model_id: str, predictions: np.ndarray,
                                 actuals: np.ndarray, model_type: ModelType) -> Dict[str, float]:
        """성능 모니터링"""
        metrics = {}
        
        if model_type == ModelType.CLASSIFICATION:
            metrics['accuracy'] = accuracy_score(actuals, predictions)
            metrics['f1_score'] = f1_score(actuals, predictions, average='weighted')
        elif model_type in [ModelType.REGRESSION, ModelType.TIME_SERIES]:
            metrics['mse'] = mean_squared_error(actuals, predictions)
            metrics['rmse'] = np.sqrt(metrics['mse'])
            metrics['mae'] = np.mean(np.abs(actuals - predictions))
            
        # 데이터 드리프트 감지
        drift_score = self._detect_drift(predictions, actuals)
        metrics['drift_score'] = drift_score
        
        # 모니터링 데이터 저장
        if model_id not in self.monitoring_data:
            self.monitoring_data[model_id] = []
            
        monitoring_entry = {
            'timestamp': datetime.now(),
            'metrics': metrics,
            'sample_size': len(predictions)
        }
        self.monitoring_data[model_id].append(monitoring_entry)
        
        # 알림 확인
        await self._check_alerts(model_id, metrics)
        
        return metrics
        
    def _detect_drift(self, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """데이터 드리프트 감지"""
        # 간단한 KS 테스트 기반 드리프트 점수
        from scipy import stats
        ks_statistic, p_value = stats.ks_2samp(predictions, actuals)
        return ks_statistic
        
    async def _check_alerts(self, model_id: str, metrics: Dict[str, float]):
        """알림 확인"""
        alerts = []
        
        # 이전 메트릭과 비교
        if len(self.monitoring_data[model_id]) > 1:
            prev_metrics = self.monitoring_data[model_id][-2]['metrics']
            
            # 정확도 하락 확인
            if 'accuracy' in metrics and 'accuracy' in prev_metrics:
                accuracy_drop = prev_metrics['accuracy'] - metrics['accuracy']
                if accuracy_drop > self.alert_thresholds['accuracy_drop']:
                    alerts.append({
                        'type': 'accuracy_drop',
                        'severity': 'high',
                        'message': f'Accuracy dropped by {accuracy_drop:.2%}',
                        'current_value': metrics['accuracy'],
                        'previous_value': prev_metrics['accuracy']
                    })
                    
        # 드리프트 확인
        if metrics.get('drift_score', 0) > 0.1:
            alerts.append({
                'type': 'data_drift',
                'severity': 'medium',
                'message': f'Data drift detected: {metrics["drift_score"]:.3f}',
                'current_value': metrics['drift_score']
            })
            
        # 알림 전송
        for alert in alerts:
            for callback in self.alert_callbacks:
                await callback(model_id, alert)
                
    def get_monitoring_report(self, model_id: str, hours: int = 24) -> Dict[str, Any]:
        """모니터링 리포트"""
        if model_id not in self.monitoring_data:
            return {'error': 'No monitoring data found'}
            
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_data = [
            entry for entry in self.monitoring_data[model_id]
            if entry['timestamp'] >= cutoff
        ]
        
        if not recent_data:
            return {'error': 'No recent data'}
            
        # 메트릭 집계
        metrics_summary = {}
        for metric_name in recent_data[0]['metrics'].keys():
            values = [entry['metrics'][metric_name] for entry in recent_data]
            metrics_summary[metric_name] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'trend': 'stable'  # 추세 분석 추가 가능
            }
            
        return {
            'model_id': model_id,
            'period_hours': hours,
            'total_predictions': sum(entry['sample_size'] for entry in recent_data),
            'metrics_summary': metrics_summary,
            'last_updated': recent_data[-1]['timestamp']
        }


class ModelDeployer:
    """모델 배포 관리"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.deployments = {}
        self.deployment_configs = {}
        
    async def deploy_model(self, model_id: str, version: str, 
                          config: Dict[str, Any]) -> Dict[str, Any]:
        """모델 배포"""
        logger.info(f"Deploying model {model_id} version {version}")
        
        # 모델 조회
        model_version = self.registry.get_model(model_id, version)
        
        # 배포 구성
        deployment_id = f"{model_id}-{version}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        deployment = {
            'deployment_id': deployment_id,
            'model_id': model_id,
            'version': version,
            'config': config,
            'status': 'deploying',
            'created_at': datetime.now()
        }
        
        self.deployments[deployment_id] = deployment
        
        try:
            # 모델 로드
            model = await self._load_model(model_version.model_path)
            
            # 헬스 체크
            health_check = await self._health_check(model, config)
            if not health_check['healthy']:
                raise Exception(f"Health check failed: {health_check['error']}")
                
            # 배포 실행 (실제로는 Kubernetes, Docker 등 사용)
            if config.get('deployment_type') == 'api':
                endpoint = await self._deploy_as_api(model, deployment_id, config)
                deployment['endpoint'] = endpoint
            elif config.get('deployment_type') == 'batch':
                deployment['batch_config'] = config.get('batch_config', {})
                
            # 상태 업데이트
            deployment['status'] = 'deployed'
            model_version.promote_to_production()
            
            logger.info(f"Model {model_id} version {version} deployed successfully")
            
            return deployment
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            deployment['status'] = 'failed'
            deployment['error'] = str(e)
            raise
            
    async def _load_model(self, model_path: str):
        """모델 로드"""
        with open(model_path, 'rb') as f:
            return pickle.load(f)
            
    async def _health_check(self, model, config: Dict[str, Any]) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            # 간단한 예측 테스트
            test_input = config.get('test_input')
            if test_input and hasattr(model, 'predict'):
                _ = model.predict(test_input)
                
            return {'healthy': True}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
            
    async def _deploy_as_api(self, model, deployment_id: str, 
                           config: Dict[str, Any]) -> str:
        """API로 배포"""
        # 실제로는 FastAPI 서버 생성 및 Docker 컨테이너 실행
        port = config.get('port', 8000)
        endpoint = f"http://localhost:{port}/predict"
        
        # 배포 시뮬레이션
        await asyncio.sleep(2)
        
        return endpoint
        
    async def rollback_deployment(self, deployment_id: str):
        """배포 롤백"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment {deployment_id} not found")
            
        deployment = self.deployments[deployment_id]
        deployment['status'] = 'rolled_back'
        deployment['rolled_back_at'] = datetime.now()
        
        logger.info(f"Deployment {deployment_id} rolled back")
        
    def get_active_deployments(self) -> List[Dict[str, Any]]:
        """활성 배포 목록"""
        return [
            d for d in self.deployments.values()
            if d['status'] == 'deployed'
        ]


class ExperimentTracker:
    """실험 추적"""
    
    def __init__(self, tracking_uri: str = "./mlruns"):
        self.tracking_uri = tracking_uri
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient()
        
    def create_experiment(self, name: str, description: str) -> str:
        """실험 생성"""
        return mlflow.create_experiment(
            name=name,
            artifact_location=f"{self.tracking_uri}/{name}",
            tags={"description": description}
        )
        
    def start_run(self, experiment_id: str, run_name: str) -> str:
        """실행 시작"""
        mlflow.start_run(
            experiment_id=experiment_id,
            run_name=run_name
        )
        return mlflow.active_run().info.run_id
        
    def log_params(self, params: Dict[str, Any]):
        """파라미터 로깅"""
        for key, value in params.items():
            mlflow.log_param(key, value)
            
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """메트릭 로깅"""
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=step)
            
    def log_model(self, model, artifact_path: str, model_type: str = "sklearn"):
        """모델 로깅"""
        if model_type == "sklearn":
            mlflow.sklearn.log_model(model, artifact_path)
        elif model_type == "pytorch":
            mlflow.pytorch.log_model(model, artifact_path)
        else:
            mlflow.log_artifact(model, artifact_path)
            
    def end_run(self):
        """실행 종료"""
        mlflow.end_run()
        
    def get_best_run(self, experiment_id: str, metric: str) -> Dict[str, Any]:
        """최고 성능 실행 조회"""
        runs = self.client.search_runs(
            experiment_ids=[experiment_id],
            order_by=[f"metrics.{metric} DESC"],
            max_results=1
        )
        
        if runs:
            run = runs[0]
            return {
                'run_id': run.info.run_id,
                'metrics': run.data.metrics,
                'params': run.data.params,
                'tags': run.data.tags
            }
        return None


class ModelManager:
    """통합 모델 관리자"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 컴포넌트 초기화
        self.registry = ModelRegistry(
            self.config.get('registry_path', './model_registry')
        )
        self.monitor = ModelMonitor()
        self.deployer = ModelDeployer(self.registry)
        self.experiment_tracker = ExperimentTracker(
            self.config.get('tracking_uri', './mlruns')
        )
        
        # 스케줄러
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        
        # 알림 설정
        self.monitor.add_alert_callback(self._send_alert)
        
    async def train_and_register_model(self, model_id: str, model_type: ModelType,
                                     train_data: Any, params: Dict[str, Any]) -> str:
        """모델 학습 및 등록"""
        # 실험 시작
        experiment_id = self.experiment_tracker.create_experiment(
            name=f"{model_id}_training",
            description=f"Training {model_type.value} model"
        )
        
        run_id = self.experiment_tracker.start_run(experiment_id, f"{model_id}_run")
        
        try:
            # 파라미터 로깅
            self.experiment_tracker.log_params(params)
            
            # 모델 학습 (시뮬레이션)
            logger.info(f"Training {model_id} model...")
            await asyncio.sleep(5)  # 학습 시뮬레이션
            
            # 메트릭 로깅
            metrics = {
                'accuracy': 0.95,
                'loss': 0.05,
                'training_time': 5.0
            }
            self.experiment_tracker.log_metrics(metrics)
            
            # 모델 저장
            model_path = f"./temp_models/{model_id}_{run_id}.pkl"
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # 더미 모델 저장
            with open(model_path, 'wb') as f:
                pickle.dump({'model': 'dummy', 'params': params}, f)
                
            # 모델 등록
            version = f"1.0.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            metadata = {
                'model_type': model_type.value,
                'mlflow_run_id': run_id,
                'metrics': metrics,
                'params': params
            }
            
            model_version = self.registry.register_model(
                model_id=model_id,
                version=version,
                model_path=model_path,
                metadata=metadata
            )
            
            self.experiment_tracker.end_run()
            
            logger.info(f"Model {model_id} version {version} trained and registered")
            return version
            
        except Exception as e:
            self.experiment_tracker.end_run()
            logger.error(f"Training failed: {str(e)}")
            raise
            
    async def deploy_model(self, model_id: str, version: Optional[str] = None,
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """모델 배포"""
        if config is None:
            config = {
                'deployment_type': 'api',
                'port': 8000,
                'replicas': 1,
                'test_input': [[1, 2, 3, 4]]  # 테스트 입력
            }
            
        deployment = await self.deployer.deploy_model(
            model_id=model_id,
            version=version or 'latest',
            config=config
        )
        
        # 모니터링 스케줄 설정
        self.scheduler.add_job(
            self._monitor_deployment,
            CronTrigger(minute='*/5'),  # 5분마다
            args=[deployment['deployment_id']],
            id=f"monitor_{deployment['deployment_id']}"
        )
        
        return deployment
        
    async def _monitor_deployment(self, deployment_id: str):
        """배포 모니터링"""
        logger.info(f"Monitoring deployment {deployment_id}")
        
        # 시뮬레이션 데이터
        predictions = np.random.rand(100)
        actuals = predictions + np.random.normal(0, 0.1, 100)
        
        deployment = self.deployer.deployments.get(deployment_id)
        if deployment:
            metrics = await self.monitor.monitor_performance(
                model_id=deployment['model_id'],
                predictions=predictions,
                actuals=actuals,
                model_type=ModelType.REGRESSION
            )
            
            logger.info(f"Monitoring metrics: {metrics}")
            
    async def _send_alert(self, model_id: str, alert: Dict[str, Any]):
        """알림 전송"""
        logger.warning(f"Alert for {model_id}: {alert}")
        
        # 이메일 알림 (설정된 경우)
        if self.config.get('email_alerts'):
            await self._send_email_alert(model_id, alert)
            
    async def _send_email_alert(self, model_id: str, alert: Dict[str, Any]):
        """이메일 알림"""
        # 실제 구현 시 SMTP 설정 필요
        pass
        
    def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """모델 상태 조회"""
        # 모델 버전 정보
        versions = []
        if model_id in self.registry.models:
            for version_str, model_version in self.registry.models[model_id].items():
                versions.append({
                    'version': version_str,
                    'status': model_version.status.value,
                    'created_at': model_version.created_at,
                    'metrics': model_version.metrics.get_latest_metrics()
                })
                
        # 배포 정보
        deployments = [
            d for d in self.deployer.deployments.values()
            if d['model_id'] == model_id
        ]
        
        # 모니터링 정보
        monitoring_report = self.monitor.get_monitoring_report(model_id)
        
        return {
            'model_id': model_id,
            'versions': versions,
            'deployments': deployments,
            'monitoring': monitoring_report
        }
        
    def cleanup_old_models(self, days: int = 30):
        """오래된 모델 정리"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for model_id, versions in self.registry.models.items():
            for version_str, model_version in versions.items():
                if (model_version.created_at < cutoff and 
                    model_version.status == ModelStatus.ARCHIVED):
                    # 모델 파일 삭제
                    if os.path.exists(model_version.model_path):
                        os.remove(model_version.model_path)
                    logger.info(f"Cleaned up {model_id} version {version_str}")