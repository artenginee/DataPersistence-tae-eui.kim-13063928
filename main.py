"""POC #2 — 데이터 영속성 (Data Persistence) CRUD 콘솔 데모"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.db_manager import DatabaseManager
from src.repositories import SampleRepository, OrderRepository, ProductionJobRepository
from src.models import Sample, Order, OrderStatus, ProductionJob, JobStatus
from src.utils.exceptions import NotFoundError, ValidationError, DatabaseError


# ── UI 헬퍼 ───────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def header(title: str):
    print(f"\n{'=' * 50}\n  {title}\n{'=' * 50}")

def print_table(rows: list[dict]):
    if not rows:
        print("  (데이터 없음)")
        return
    keys = list(rows[0].keys())
    widths = {k: max(len(str(k)), max(len(str(r.get(k, ""))) for r in rows)) for k in keys}
    sep = "+-" + "-+-".join("-" * widths[k] for k in keys) + "-+"
    print(sep)
    print("| " + " | ".join(str(k).ljust(widths[k]) for k in keys) + " |")
    print(sep)
    for r in rows:
        print("| " + " | ".join(str(r.get(k, "")).ljust(widths[k]) for k in keys) + " |")
    print(sep)

def input_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("  숫자를 입력해 주세요.")

def input_float(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("  숫자를 입력해 주세요.")

def pause():
    input("\n  [Enter] 를 누르면 계속합니다...")


# ── 표시 포맷 ─────────────────────────────────────────────────────────────────

def fmt_sample(s: Sample) -> dict:
    return {
        "ID":         s.sample_id,
        "시료명":      s.name,
        "생산시간(분)": s.avg_production_time,
        "수율":        f"{s.yield_rate * 100:.1f}%",
        "재고":        s.stock,
        "설명":        s.description,
        "등록일":      s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "-",
    }

def fmt_order(o: Order) -> dict:
    return {
        "ID":     o.order_id,
        "고객명":  o.customer_name,
        "시료ID":  o.sample_id,
        "시료명":  o.sample_name or "-",
        "수량":    o.quantity,
        "상태":    o.status.value,
        "접수일":  o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "-",
        "수정일":  o.updated_at.strftime("%Y-%m-%d %H:%M") if o.updated_at else "-",
    }

def fmt_job(j: ProductionJob) -> dict:
    rate = 0.0 if j.planned_quantity == 0 else round(j.actual_quantity / j.planned_quantity * 100, 1)
    return {
        "JobID":    j.job_id,
        "주문ID":   j.order_id,
        "고객명":   j.customer_name or "-",
        "시료명":   j.sample_name or "-",
        "계획수량":  j.planned_quantity,
        "실적수량":  j.actual_quantity,
        "진행률":   f"{rate}%",
        "예상시간":  f"{j.total_time_min:.1f}분",
        "상태":     j.status.value,
        "큐순번":   j.queue_order,
        "등록일":   j.created_at.strftime("%Y-%m-%d %H:%M") if j.created_at else "-",
    }


# ── 시료 관리 ─────────────────────────────────────────────────────────────────

def menu_sample(repo: SampleRepository):
    while True:
        header("시료(Sample) 관리")
        print("  1. 전체 목록 조회")
        print("  2. ID 로 조회")
        print("  3. 이름 검색")
        print("  4. 시료 등록")
        print("  5. 시료 수정")
        print("  6. 재고 변경 (delta)")
        print("  7. 시료 삭제")
        print("  0. 이전 메뉴")
        choice = input("\n  선택 > ").strip()

        if choice == "1":
            header("시료 목록")
            print_table([fmt_sample(s) for s in repo.find_all()])
            pause()

        elif choice == "2":
            sid = input_int("  시료 ID > ")
            s = repo.find_by_id(sid)
            print_table([fmt_sample(s)] if s else [])
            if not s:
                print(f"  ID={sid} 없음")
            pause()

        elif choice == "3":
            keyword = input("  검색 키워드 > ").strip()
            print_table([fmt_sample(s) for s in repo.find_by_name(keyword)])
            pause()

        elif choice == "4":
            header("시료 등록")
            try:
                s = Sample(
                    name=input("  시료명 > ").strip(),
                    avg_production_time=input_float("  평균 생산시간 (분/개) > "),
                    yield_rate=input_float("  수율 (예: 0.85) > "),
                    stock=input_int("  초기 재고 > "),
                    description=input("  설명 (선택) > ").strip(),
                )
                created = repo.create(s)
                print(f"\n  등록 완료 → ID={created.sample_id}")
            except (ValidationError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "5":
            sid = input_int("  수정할 시료 ID > ")
            s = repo.find_by_id(sid)
            if not s:
                print(f"  ID={sid} 없음")
                pause()
                continue
            print("  [Enter] 로 기존 값 유지")
            try:
                name = input(f"  시료명 [{s.name}] > ").strip() or s.name
                apt = input(f"  생산시간 [{s.avg_production_time}] > ").strip()
                yr  = input(f"  수율     [{s.yield_rate}] > ").strip()
                stk = input(f"  재고     [{s.stock}] > ").strip()
                dsc = input(f"  설명     [{s.description}] > ").strip()
                s.name = name
                s.avg_production_time = float(apt) if apt else s.avg_production_time
                s.yield_rate  = float(yr)  if yr  else s.yield_rate
                s.stock       = int(stk)   if stk else s.stock
                s.description = dsc or s.description
                repo.update(s)
                print("  수정 완료")
            except (ValidationError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "6":
            sid = input_int("  시료 ID > ")
            s = repo.find_by_id(sid)
            if not s:
                print(f"  ID={sid} 없음")
                pause()
                continue
            print(f"  현재 재고: {s.stock}")
            delta = input_int("  변경량 (양수=입고, 음수=차감) > ")
            try:
                new_stock = repo.update_stock(sid, delta)
                print(f"  변경 완료 → 재고={new_stock}")
            except (NotFoundError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "7":
            sid = input_int("  삭제할 시료 ID > ")
            if input(f"  ID={sid} 삭제합니까? (y/N) > ").strip().lower() == "y":
                try:
                    ok = repo.delete(sid)
                    print("  삭제 완료" if ok else "  대상 없음")
                except DatabaseError as e:
                    print(f"  오류: {e}")
            else:
                print("  취소")
            pause()

        elif choice == "0":
            break


# ── 주문 관리 ─────────────────────────────────────────────────────────────────

def menu_order(repo: OrderRepository):
    statuses = [s.value for s in OrderStatus]

    while True:
        header("주문(Order) 관리")
        print("  1. 전체 목록 조회")
        print("  2. ID 로 조회")
        print("  3. 상태별 조회")
        print("  4. 시료별 조회")
        print("  5. 주문 등록")
        print("  6. 주문 수정")
        print("  7. 상태 변경")
        print("  8. 주문 삭제")
        print("  0. 이전 메뉴")
        choice = input("\n  선택 > ").strip()

        if choice == "1":
            header("주문 목록")
            print_table([fmt_order(o) for o in repo.find_all()])
            pause()

        elif choice == "2":
            oid = input_int("  주문 ID > ")
            o = repo.find_by_id(oid)
            print_table([fmt_order(o)] if o else [])
            if not o:
                print(f"  ID={oid} 없음")
            pause()

        elif choice == "3":
            print(f"  상태: {', '.join(statuses)}")
            sv = input("  > ").strip().upper()
            try:
                print_table([fmt_order(o) for o in repo.find_by_status(OrderStatus(sv))])
            except ValueError:
                print(f"  알 수 없는 상태: {sv}")
            pause()

        elif choice == "4":
            sid = input_int("  시료 ID > ")
            print_table([fmt_order(o) for o in repo.find_by_sample(sid)])
            pause()

        elif choice == "5":
            header("주문 등록")
            try:
                o = Order(
                    customer_name=input("  고객명 > ").strip(),
                    sample_id=input_int("  시료 ID > "),
                    quantity=input_int("  수량 > "),
                )
                created = repo.create(o)
                print(f"\n  등록 완료 → ID={created.order_id}")
            except (ValidationError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "6":
            oid = input_int("  수정할 주문 ID > ")
            o = repo.find_by_id(oid)
            if not o:
                print(f"  ID={oid} 없음")
                pause()
                continue
            print("  [Enter] 로 기존 값 유지")
            try:
                cust = input(f"  고객명 [{o.customer_name}] > ").strip() or o.customer_name
                sid  = input(f"  시료 ID [{o.sample_id}] > ").strip()
                qty  = input(f"  수량    [{o.quantity}] > ").strip()
                o.customer_name = cust
                o.sample_id = int(sid) if sid else o.sample_id
                o.quantity  = int(qty) if qty else o.quantity
                repo.update(o)
                print("  수정 완료")
            except (ValidationError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "7":
            oid = input_int("  주문 ID > ")
            print(f"  상태: {', '.join(statuses)}")
            sv = input("  새 상태 > ").strip().upper()
            try:
                ok = repo.update_status(oid, OrderStatus(sv))
                print("  변경 완료" if ok else "  대상 없음")
            except (ValueError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "8":
            oid = input_int("  삭제할 주문 ID > ")
            if input(f"  ID={oid} 삭제합니까? (y/N) > ").strip().lower() == "y":
                try:
                    ok = repo.delete(oid)
                    print("  삭제 완료" if ok else "  대상 없음")
                except DatabaseError as e:
                    print(f"  오류: {e}")
            else:
                print("  취소")
            pause()

        elif choice == "0":
            break


# ── 생산 작업 큐 관리 ──────────────────────────────────────────────────────────

def menu_production(repo: ProductionJobRepository):
    job_statuses = [s.value for s in JobStatus]

    while True:
        header("생산 작업 큐(ProductionJob) 관리")
        print("  1. 전체 큐 조회 (FIFO 순)")
        print("  2. ID 로 조회")
        print("  3. 상태별 조회")
        print("  4. 주문별 조회")
        print("  5. 작업 등록")
        print("  6. 작업 수정")
        print("  7. 실적 수량 업데이트")
        print("  8. 상태 변경")
        print("  9. 작업 삭제")
        print("  0. 이전 메뉴")
        choice = input("\n  선택 > ").strip()

        if choice == "1":
            header("생산 큐 전체")
            print_table([fmt_job(j) for j in repo.find_all()])
            pause()

        elif choice == "2":
            jid = input_int("  Job ID > ")
            j = repo.find_by_id(jid)
            print_table([fmt_job(j)] if j else [])
            if not j:
                print(f"  ID={jid} 없음")
            pause()

        elif choice == "3":
            print(f"  상태: {', '.join(job_statuses)}")
            sv = input("  > ").strip().upper()
            try:
                print_table([fmt_job(j) for j in repo.find_by_status(JobStatus(sv))])
            except ValueError:
                print(f"  알 수 없는 상태: {sv}")
            pause()

        elif choice == "4":
            oid = input_int("  주문 ID > ")
            j = repo.find_by_order(oid)
            print_table([fmt_job(j)] if j else [])
            if not j:
                print("  해당 주문의 작업 없음")
            pause()

        elif choice == "5":
            header("생산 작업 등록")
            try:
                j = ProductionJob(
                    order_id=input_int("  주문 ID > "),
                    sample_id=input_int("  시료 ID > "),
                    planned_quantity=input_int("  계획 수량 > "),
                    total_time_min=input_float("  총 예상 시간 (분) > "),
                    notes=input("  비고 (선택) > ").strip(),
                )
                created = repo.create(j)
                print(f"\n  등록 완료 → JobID={created.job_id}, 큐순번={created.queue_order}")
            except (ValidationError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "6":
            jid = input_int("  수정할 Job ID > ")
            j = repo.find_by_id(jid)
            if not j:
                print(f"  ID={jid} 없음")
                pause()
                continue
            print("  [Enter] 로 기존 값 유지")
            try:
                pq  = input(f"  계획 수량  [{j.planned_quantity}] > ").strip()
                aq  = input(f"  실적 수량  [{j.actual_quantity}] > ").strip()
                tt  = input(f"  예상시간(분)[{j.total_time_min}] > ").strip()
                nt  = input(f"  비고       [{j.notes}] > ").strip()
                j.planned_quantity = int(pq)   if pq else j.planned_quantity
                j.actual_quantity  = int(aq)   if aq else j.actual_quantity
                j.total_time_min   = float(tt) if tt else j.total_time_min
                j.notes = nt or j.notes
                repo.update(j)
                print("  수정 완료")
            except (ValidationError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "7":
            jid = input_int("  Job ID > ")
            qty = input_int("  실적 수량 > ")
            try:
                ok = repo.update_actual_quantity(jid, qty)
                print("  업데이트 완료" if ok else "  대상 없음")
            except DatabaseError as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "8":
            jid = input_int("  Job ID > ")
            print(f"  상태: {', '.join(job_statuses)}")
            sv = input("  새 상태 > ").strip().upper()
            try:
                ok = repo.update_status(jid, JobStatus(sv))
                print("  변경 완료" if ok else "  대상 없음")
            except (ValueError, DatabaseError) as e:
                print(f"  오류: {e}")
            pause()

        elif choice == "9":
            jid = input_int("  삭제할 Job ID > ")
            if input(f"  ID={jid} 삭제합니까? (y/N) > ").strip().lower() == "y":
                try:
                    ok = repo.delete(jid)
                    print("  삭제 완료" if ok else "  대상 없음")
                except DatabaseError as e:
                    print(f"  오류: {e}")
            else:
                print("  취소")
            pause()

        elif choice == "0":
            break


# ── DB 현황 요약 ──────────────────────────────────────────────────────────────

def show_summary(s_repo: SampleRepository, o_repo: OrderRepository, j_repo: ProductionJobRepository):
    header("DB 현황 요약")
    print(f"  시료    : {s_repo.count()} 건")
    print(f"  주문    : {o_repo.count()} 건")
    print(f"  생산작업 : {j_repo.count()} 건")

    sc = o_repo.count_by_status()
    if sc:
        print("\n  [주문 상태별]")
        for status, cnt in sc.items():
            print(f"    {status:<12}: {cnt} 건")

    jc = j_repo.count_by_status()
    if jc:
        print("\n  [생산 큐 상태별]")
        for status, cnt in jc.items():
            print(f"    {status:<12}: {cnt} 건")
    pause()


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main():
    db = DatabaseManager.get_instance()
    s_repo = SampleRepository(db)
    o_repo = OrderRepository(db)
    j_repo = ProductionJobRepository(db)

    while True:
        clear()
        header("반도체 주문/생산 관리 — POC #2 데이터 영속성")
        print(f"  DB: {db.db_path}\n")
        print("  1. 시료(Sample) 관리")
        print("  2. 주문(Order)  관리")
        print("  3. 생산 작업 큐 관리")
        print("  4. DB 현황 요약")
        print("  0. 종료")
        choice = input("\n  선택 > ").strip()

        if choice == "1":
            menu_sample(s_repo)
        elif choice == "2":
            menu_order(o_repo)
        elif choice == "3":
            menu_production(j_repo)
        elif choice == "4":
            show_summary(s_repo, o_repo, j_repo)
        elif choice == "0":
            print("\n  종료합니다.")
            break


if __name__ == "__main__":
    main()
