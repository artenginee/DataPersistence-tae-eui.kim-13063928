# POC #2 — 데이터 영속성 (Data Persistence)

반도체 주문/생산 관리 시스템의 4개 POC 중 **두 번째 POC** 입니다.  
SQLite 기반 CRUD와 레이어별 인터페이스 설계에 집중합니다.

---

## POC 전체 구성

| POC | 담당 역할 | 저장소 |
|-----|-----------|--------|
| **#1** | MVC 스켈레톤 — Model / Controller / View 패키지 구조 | [ConsoleMVC](https://github.com/artenginee/ConsoleMVC-tae-eui.kim-13063928) |
| **#2** | **데이터 영속성 — SQLite CRUD + 인터페이스** | 현재 저장소 |
| #3 | 데이터 모니터링 Tool — 실시간 콘솔 조회 | - |
| #4 | Dummy 데이터 생성 Tool | - |

---

## 도메인 모델

```
Sample (시료)
├── sample_id, name
├── avg_production_time (분/개)
├── yield_rate (수율, 0.0 ~ 1.0)
└── stock (재고 수량)

Order (주문)
├── order_id, customer_name, sample_id, quantity
└── status: RESERVED → PRODUCING │ CONFIRMED → RELEASE
                   └→ REJECTED

ProductionJob (생산 작업 큐)
├── job_id, order_id, sample_id
├── planned_quantity, actual_quantity, total_time_min
├── queue_order (FIFO 순번)
└── status: WAITING → IN_PROGRESS → COMPLETED
```

**주문 상태 흐름**

```
[접수] RESERVED
    ├── 승인 + 재고 충분  →  CONFIRMED  →  RELEASE (출고)
    ├── 승인 + 재고 부족  →  PRODUCING  →  CONFIRMED  →  RELEASE
    └── 거절             →  REJECTED
```

---

## 프로젝트 구조

```
DataPersistence/
├── main.py                          # 메뉴 기반 CRUD 콘솔 데모
├── pytest.ini                       # 테스트 설정 (100% 커버리지 강제)
├── .coveragerc                      # coverage 제외 규칙
├── requirements.txt                 # pytest, pytest-cov
│
├── src/
│   ├── models/                      # 도메인 데이터 클래스
│   │   ├── sample.py                  Sample
│   │   ├── order.py                   Order, OrderStatus
│   │   └── production_job.py          ProductionJob, JobStatus
│   │
│   ├── interfaces/                  # ★ merge 기준 계약 (ABC)
│   │   ├── i_sample_repository.py     ISampleRepository
│   │   ├── i_order_repository.py      IOrderRepository
│   │   └── i_production_job_repository.py  IProductionJobRepository
│   │
│   ├── repositories/                # 인터페이스 SQLite 구현체
│   │   ├── base_repository.py         BaseRepository[T] (공통 CRUD ABC)
│   │   ├── sample_repository.py       SampleRepository
│   │   ├── order_repository.py        OrderRepository
│   │   └── production_job_repository.py  ProductionJobRepository
│   │
│   ├── database/
│   │   └── db_manager.py              DatabaseManager (연결·스키마·헬퍼)
│   │
│   └── utils/
│       └── exceptions.py              NotFoundError / ValidationError / DatabaseError
│
└── tests/
    ├── conftest.py                  # 공통 픽스처 (db, sample_repo, order_repo, job_repo, …)
    ├── test_exceptions.py
    ├── test_models.py
    ├── test_db_manager.py
    ├── test_sample_repository.py
    ├── test_order_repository.py
    └── test_production_job_repository.py
```

---

## 인터페이스 설계 (merge 포인트)

다른 POC와 합칠 때 **인터페이스에만 의존**하면 구현체를 교체해도 상위 레이어를 수정할 필요가 없습니다.

```python
# 인터페이스 계층 구조
BaseRepository[T]                   ← 공통 CRUD (create / find_by_id / find_all / update / delete / count)
    └── ISampleRepository           ← + find_by_name / update_stock
    └── IOrderRepository            ← + find_by_status / find_by_sample / count_by_status / update_status
    └── IProductionJobRepository    ← + find_by_status / find_waiting_queue / find_in_progress
                                         find_by_order / count_by_status / update_status / update_actual_quantity
```

| 합칠 POC | 사용하는 인터페이스 |
|----------|-------------------|
| #1 MVC Controller | `ISampleRepository`, `IOrderRepository`, `IProductionJobRepository` |
| #3 모니터링 Tool | 동일 인터페이스 read 메서드 |
| #4 Dummy 데이터 Tool | 동일 인터페이스 create 메서드 |

```python
# 사용 예시 — Controller 가 인터페이스에만 의존
from src.interfaces import ISampleRepository

class SampleController:
    def __init__(self, repo: ISampleRepository):   # 구현체 교체 자유
        self._repo = repo
```

---

## 실행 방법

### 요구 사항
- Python 3.10 이상 (외부 라이브러리 없음, 표준 `sqlite3` 사용)

### 콘솔 데모 실행

```bash
python main.py
```

```
==================================================
  반도체 주문/생산 관리 — POC #2 데이터 영속성
==================================================
  DB: data/semiconductor.db

  1. 시료(Sample) 관리
  2. 주문(Order)  관리
  3. 생산 작업 큐 관리
  4. DB 현황 요약
  0. 종료
```

> DB 파일은 첫 실행 시 `data/semiconductor.db` 에 자동 생성됩니다.

---

## 테스트 실행

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 전체 테스트 + 커버리지

```bash
pytest
```

### 결과

```
132 passed in 7s
TOTAL    387    0   100%
Required test coverage of 100% reached. Total coverage: 100.00%
```

### 테스트 구성

| 파일 | 검증 대상 | 테스트 수 |
|------|-----------|-----------|
| `test_exceptions.py` | 예외 클래스 메시지 및 타입 | 7 |
| `test_models.py` | 모델 validate() 경계값 | 19 |
| `test_db_manager.py` | DB 초기화, 싱글턴, 헬퍼 | 14 |
| `test_sample_repository.py` | 시료 CRUD 전 경로 | 26 |
| `test_order_repository.py` | 주문 CRUD 전 경로 | 29 |
| `test_production_job_repository.py` | 생산 큐 CRUD 전 경로 | 37 |

**테스트 전략**
- 정상 경로: DB 반영 값 검증
- 경계 조건: 존재하지 않는 ID, 빈 결과, 중복 키
- 오류 경로: `monkeypatch` 로 DB 예외를 주입해 `DatabaseError` 래핑 검증

---

## 주요 설계 결정

| 항목 | 선택 | 이유 |
|------|------|------|
| DB | SQLite | 외부 의존성 없이 로컬 실행 가능 |
| 패턴 | Repository Pattern | 인터페이스와 구현을 분리해 merge 시 상위 레이어 변경 최소화 |
| 연결 관리 | `query()` / `query_one()` 헬퍼 | 읽기 연결 자동 close, 쓰기는 `with conn:` 트랜잭션 |
| 비즈니스 로직 | 포함하지 않음 | POC 역할 분리 원칙 — 로직은 MVC Controller(POC #1) 에 위치 |
