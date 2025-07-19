#!/usr/bin/env python3
"""
MLOps 플랫폼 사용 예제
"""
import asyncio
import numpy as np
from datetime import datetime, timedelta
import logging
from model_manager import (
    ModelManager, ModelType, ModelStatus,
    ModelRegistry, ModelMonitor, ExperimentTracker
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_model_lifecycle_demo():
    """기본 모델 생명주기 데모"""
    print("=== 모델 생명주기 관리 데모 ===\n")
    
    # 모델 매니저 초기화
    model_manager = ModelManager({
        'registry_path': './model_registry_demo',
        'tracking_uri': './mlruns_demo'
    })
    
    # 1. 모델 학습 및 등록
    print("1. 모델 학습 및 등록")
    model_id = "sales_predictor"
    version = await model_manager.train_and_register_model(
        model_id=model_id,
        model_type=ModelType.TIME_SERIES,
        train_data=None,  # 실제로는 학습 데이터
        params={
            'algorithm': 'LSTM',
            'epochs': 100,
            'learning_rate': 0.001,
            'batch_size': 32
        }
    )
    print(f"✓ 모델 {model_id} 버전 {version} 등록 완료\n")
    
    # 2. 모델 배포
    print("2. 모델 배포")
    deployment = await model_manager.deploy_model(
        model_id=model_id,
        version=version,
        config={
            'deployment_type': 'api',
            'port': 8001,
            'replicas': 2,
            'memory_limit': '2Gi',
            'cpu_limit': '1000m'
        }
    )
    print(f"✓ 배포 완료: {deployment['deployment_id']}")
    print(f"  엔드포인트: {deployment.get('endpoint', 'N/A')}\n")
    
    # 3. 모델 상태 확인
    print("3. 모델 상태 확인")
    status = model_manager.get_model_status(model_id)
    print(f"모델 ID: {status['model_id']}")
    print(f"버전 수: {len(status['versions'])}")
    print(f"활성 배포: {len(status['deployments'])}")
    
    # 4. 모니터링 시뮬레이션
    print("\n4. 모델 성능 모니터링")
    for i in range(3):
        # 예측 시뮬레이션
        predictions = np.random.rand(50) * 100
        actuals = predictions + np.random.normal(0, 5, 50)
        
        metrics = await model_manager.monitor.monitor_performance(
            model_id=model_id,
            predictions=predictions,
            actuals=actuals,
            model_type=ModelType.TIME_SERIES
        )
        
        print(f"  반복 {i+1} - RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}")
        await asyncio.sleep(1)
    
    # 5. 모니터링 리포트
    print("\n5. 모니터링 리포트")
    report = model_manager.monitor.get_monitoring_report(model_id, hours=1)
    if 'metrics_summary' in report:
        print("메트릭 요약:")
        for metric, stats in report['metrics_summary'].items():
            print(f"  {metric}: 평균={stats['mean']:.3f}, 표준편차={stats['std']:.3f}")


async def experiment_tracking_demo():
    """실험 추적 데모"""
    print("\n=== 실험 추적 데모 ===\n")
    
    tracker = ExperimentTracker('./mlruns_experiment_demo')
    
    # 실험 생성
    experiment_id = tracker.create_experiment(
        name="hyperparameter_tuning",
        description="하이퍼파라미터 튜닝 실험"
    )
    
    # 여러 실행으로 하이퍼파라미터 탐색
    best_run = None
    best_metric = float('inf')
    
    hyperparameters = [
        {'learning_rate': 0.001, 'batch_size': 32, 'epochs': 50},
        {'learning_rate': 0.01, 'batch_size': 64, 'epochs': 50},
        {'learning_rate': 0.005, 'batch_size': 32, 'epochs': 100}
    ]
    
    for i, params in enumerate(hyperparameters):
        print(f"\n실행 {i+1}: {params}")
        
        # 실행 시작
        run_id = tracker.start_run(experiment_id, f"run_{i+1}")
        
        # 파라미터 로깅
        tracker.log_params(params)
        
        # 학습 시뮬레이션 (에폭별 메트릭)
        for epoch in range(5):  # 간단히 5 에폭만
            # 메트릭 시뮬레이션
            loss = np.random.exponential(0.1) * (1 - epoch/10)
            accuracy = 0.8 + epoch * 0.02 + np.random.normal(0, 0.01)
            
            tracker.log_metrics({
                'loss': loss,
                'accuracy': accuracy
            }, step=epoch)
            
            print(f"  Epoch {epoch+1}: loss={loss:.3f}, accuracy={accuracy:.3f}")
        
        # 최종 메트릭
        final_loss = loss
        tracker.log_metrics({
            'final_loss': final_loss,
            'final_accuracy': accuracy
        })
        
        # 최고 성능 추적
        if final_loss < best_metric:
            best_metric = final_loss
            best_run = {
                'run_id': run_id,
                'params': params,
                'loss': final_loss
            }
        
        tracker.end_run()
    
    print(f"\n최고 성능 실행:")
    print(f"  Run ID: {best_run['run_id']}")
    print(f"  파라미터: {best_run['params']}")
    print(f"  Loss: {best_run['loss']:.3f}")


async def model_versioning_demo():
    """모델 버전 관리 데모"""
    print("\n=== 모델 버전 관리 데모 ===\n")
    
    registry = ModelRegistry('./model_registry_version_demo')
    
    # 여러 버전 등록
    model_id = "customer_churn_model"
    versions = ["1.0.0", "1.0.1", "1.1.0", "2.0.0"]
    
    for i, version in enumerate(versions):
        print(f"버전 {version} 등록 중...")
        
        # 모델 파일 생성 (시뮬레이션)
        import pickle
        import os
        
        model_dir = f"./temp_models_{model_id}"
        os.makedirs(model_dir, exist_ok=True)
        model_path = f"{model_dir}/model_v{version}.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump({
                'version': version,
                'accuracy': 0.85 + i * 0.02,
                'created_at': datetime.now()
            }, f)
        
        # 모델 등록
        model_version = registry.register_model(
            model_id=model_id,
            version=version,
            model_path=model_path,
            metadata={
                'algorithm': 'XGBoost',
                'accuracy': 0.85 + i * 0.02,
                'f1_score': 0.82 + i * 0.02,
                'training_data': 'customer_data_v2',
                'features': ['recency', 'frequency', 'monetary', 'tenure']
            }
        )
        
        # 버전 2.0.0을 프로덕션으로 승격
        if version == "2.0.0":
            model_version.promote_to_production()
            print(f"  ✓ 버전 {version} 프로덕션으로 승격")
        
        await asyncio.sleep(0.5)
    
    # 모델 목록 확인
    print("\n등록된 모델 버전:")
    models = registry.list_models()
    for model in models:
        print(f"  - {model['model_id']} v{model['version']}: "
              f"상태={model['status']}, "
              f"정확도={model['metadata'].get('accuracy', 'N/A')}")
    
    # 프로덕션 모델 조회
    print("\n프로덕션 모델 조회:")
    prod_model = registry.get_model(model_id)  # 버전 없이 조회하면 프로덕션 버전
    print(f"  모델: {prod_model.model_id}")
    print(f"  버전: {prod_model.version}")
    print(f"  상태: {prod_model.status.value}")


async def monitoring_alerts_demo():
    """모니터링 및 알림 데모"""
    print("\n=== 모니터링 및 알림 데모 ===\n")
    
    monitor = ModelMonitor()
    
    # 알림 핸들러 설정
    alerts_received = []
    
    async def alert_handler(model_id: str, alert: Dict[str, Any]):
        alerts_received.append(alert)
        print(f"\n🚨 알림 발생!")
        print(f"  모델: {model_id}")
        print(f"  유형: {alert['type']}")
        print(f"  심각도: {alert['severity']}")
        print(f"  메시지: {alert['message']}")
    
    monitor.add_alert_callback(alert_handler)
    
    # 정상 성능 시뮬레이션
    model_id = "recommendation_model"
    print("1. 정상 성능 모니터링")
    
    for i in range(3):
        predictions = np.random.rand(100)
        actuals = predictions + np.random.normal(0, 0.05, 100)  # 작은 오차
        
        metrics = await monitor.monitor_performance(
            model_id=model_id,
            predictions=predictions,
            actuals=actuals,
            model_type=ModelType.REGRESSION
        )
        print(f"  반복 {i+1}: RMSE={metrics['rmse']:.3f}")
        await asyncio.sleep(0.5)
    
    # 성능 저하 시뮬레이션
    print("\n2. 성능 저하 시뮬레이션")
    
    # 먼저 좋은 성능 기록
    good_predictions = np.random.rand(100)
    good_actuals = good_predictions + np.random.normal(0, 0.05, 100)
    
    await monitor.monitor_performance(
        model_id=model_id,
        predictions=good_predictions,
        actuals=good_actuals,
        model_type=ModelType.CLASSIFICATION
    )
    
    # 성능 저하
    bad_predictions = np.random.rand(100)
    bad_actuals = np.ones(100) - bad_predictions  # 반대 예측
    
    await monitor.monitor_performance(
        model_id=model_id,
        predictions=bad_predictions,
        actuals=bad_actuals,
        model_type=ModelType.CLASSIFICATION
    )
    
    # 데이터 드리프트 시뮬레이션
    print("\n3. 데이터 드리프트 시뮬레이션")
    
    # 분포가 다른 데이터
    drift_predictions = np.random.normal(0.8, 0.1, 100)  # 다른 평균
    drift_actuals = np.random.normal(0.2, 0.1, 100)  # 매우 다른 분포
    
    metrics = await monitor.monitor_performance(
        model_id=model_id,
        predictions=drift_predictions,
        actuals=drift_actuals,
        model_type=ModelType.REGRESSION
    )
    
    print(f"\n총 {len(alerts_received)}개의 알림 발생")


async def deployment_strategies_demo():
    """배포 전략 데모"""
    print("\n=== 배포 전략 데모 ===\n")
    
    model_manager = ModelManager()
    
    # A/B 테스트 배포
    print("1. A/B 테스트 배포")
    
    # 모델 A (현재 버전)
    version_a = await model_manager.train_and_register_model(
        model_id="pricing_model",
        model_type=ModelType.REGRESSION,
        train_data=None,
        params={'version': 'A', 'algorithm': 'RandomForest'}
    )
    
    # 모델 B (신규 버전)
    version_b = await model_manager.train_and_register_model(
        model_id="pricing_model",
        model_type=ModelType.REGRESSION,
        train_data=None,
        params={'version': 'B', 'algorithm': 'XGBoost'}
    )
    
    # 두 모델 동시 배포 (트래픽 분할)
    deployment_a = await model_manager.deploy_model(
        model_id="pricing_model",
        version=version_a,
        config={
            'deployment_type': 'api',
            'port': 8002,
            'traffic_percentage': 70  # 70% 트래픽
        }
    )
    
    deployment_b = await model_manager.deploy_model(
        model_id="pricing_model",
        version=version_b,
        config={
            'deployment_type': 'api',
            'port': 8003,
            'traffic_percentage': 30  # 30% 트래픽
        }
    )
    
    print(f"  ✓ 모델 A (v{version_a}): 70% 트래픽")
    print(f"  ✓ 모델 B (v{version_b}): 30% 트래픽")
    
    # 카나리 배포
    print("\n2. 카나리 배포")
    
    # 단계적 트래픽 증가
    traffic_stages = [10, 25, 50, 100]
    
    for stage, traffic in enumerate(traffic_stages):
        print(f"  스테이지 {stage+1}: {traffic}% 트래픽")
        
        # 성능 모니터링 (시뮬레이션)
        error_rate = np.random.uniform(0.01, 0.03)  # 1-3% 오류율
        
        if error_rate > 0.025:  # 임계값 초과
            print(f"    ⚠️ 오류율 {error_rate:.1%} - 롤백 필요")
            await model_manager.deployer.rollback_deployment(deployment_b['deployment_id'])
            break
        else:
            print(f"    ✓ 오류율 {error_rate:.1%} - 정상")
        
        await asyncio.sleep(1)
    
    # 블루-그린 배포
    print("\n3. 블루-그린 배포")
    
    # 현재 프로덕션 (블루)
    print("  블루 환경 (현재 프로덕션) 활성")
    
    # 새 버전 준비 (그린)
    print("  그린 환경 준비 중...")
    await asyncio.sleep(2)
    
    # 스위치
    print("  트래픽 전환: 블루 → 그린")
    print("  ✓ 배포 완료 (다운타임 없음)")


async def model_lifecycle_automation_demo():
    """모델 생명주기 자동화 데모"""
    print("\n=== 모델 생명주기 자동화 데모 ===\n")
    
    model_manager = ModelManager({
        'email_alerts': False  # 이메일 알림 비활성화
    })
    
    # 자동 재학습 스케줄
    print("1. 자동 재학습 스케줄 설정")
    
    from apscheduler.triggers.cron import CronTrigger
    
    async def auto_retrain():
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] 자동 재학습 시작")
        version = await model_manager.train_and_register_model(
            model_id="auto_model",
            model_type=ModelType.TIME_SERIES,
            train_data=None,
            params={'auto_retrain': True}
        )
        print(f"  새 버전 {version} 학습 완료")
    
    # 매일 새벽 2시 재학습 (데모에서는 즉시 실행)
    model_manager.scheduler.add_job(
        auto_retrain,
        CronTrigger(second='*/10'),  # 데모: 10초마다
        id='auto_retrain_job',
        max_instances=1
    )
    
    print("  ✓ 자동 재학습 스케줄 등록 (10초마다)")
    
    # 모델 성능 기반 자동 교체
    print("\n2. 성능 기반 자동 모델 교체")
    
    current_model = "model_v1"
    new_model = "model_v2"
    
    # 성능 비교
    current_performance = 0.85
    new_performance = 0.88
    
    if new_performance > current_performance * 1.02:  # 2% 이상 개선
        print(f"  ✓ 신규 모델 성능 {new_performance:.2%} > "
              f"현재 모델 {current_performance:.2%}")
        print("  자동으로 신규 모델로 교체")
    else:
        print("  현재 모델 유지")
    
    # 오래된 모델 정리
    print("\n3. 오래된 모델 자동 정리")
    model_manager.cleanup_old_models(days=30)
    print("  ✓ 30일 이상 된 아카이브 모델 정리 완료")
    
    # 10초 대기 (자동 재학습 확인)
    await asyncio.sleep(12)
    
    # 스케줄러 정리
    model_manager.scheduler.remove_job('auto_retrain_job')


async def main():
    """메인 함수"""
    # 기본 모델 생명주기 데모
    await basic_model_lifecycle_demo()
    
    # 실험 추적 데모
    await experiment_tracking_demo()
    
    # 모델 버전 관리 데모
    await model_versioning_demo()
    
    # 모니터링 및 알림 데모
    await monitoring_alerts_demo()
    
    # 배포 전략 데모
    await deployment_strategies_demo()
    
    # 모델 생명주기 자동화 데모
    await model_lifecycle_automation_demo()
    
    print("\n=== 모든 데모 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())