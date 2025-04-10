import argparse
from train import train_model

def get_progress_bar(current, total, bar_length=30):
    ratio = current / total
    filled = int(bar_length * ratio)
    bar = "#" * filled + "-" * (bar_length - filled)
    percent = int(ratio * 100)
    return f"[{bar}] {percent}%"

def run():
    parser = argparse.ArgumentParser(description="📚 감정 분류 모델 학습 실행기")
    parser.add_argument('--model', type=str, default='all', choices=['kcbert', 'koelectra', 'klue', 'all'],
                        help='학습할 모델명 또는 all')
    parser.add_argument('--level', type=str, default='all', choices=['대분류', '중분류', '소분류', 'all'],
                        help='학습할 감정 레벨 또는 all')
    parser.add_argument('--epochs', type=int, default=3, help='학습할 에폭 수')
    parser.add_argument('--batch_size', type=int, default=16, help='배치 사이즈')
    parser.add_argument('--repeat_fail', action='store_true', help='실패한 조합 반복 재시도')
    parser.add_argument('--max_retry', type=int, default=2, help='실패 조합의 최대 반복 횟수')

    args = parser.parse_args()

    model_list = ['kcbert', 'koelectra', 'klue'] if args.model == 'all' else [args.model]
    level_list = ['대분류', '중분류', '소분류'] if args.level == 'all' else [args.level]

    def run_jobs(model_level_pairs):
        total = len(model_level_pairs)
        success, fail = 0, 0
        fail_log = []

        for idx, (model_name, label_level) in enumerate(model_level_pairs, start=1):
            progress = get_progress_bar(idx - 1, total)
            print(f"\n============================")
            print(f"▶️ [{idx}/{total}] {progress}")
            print(f"🚀 모델: {model_name.upper()} | 레벨: {label_level}")
            print(f"============================")

            try:
                train_model(
                    model_name=model_name,
                    label_level=label_level,
                    epochs=args.epochs,
                    batch_size=args.batch_size
                )
                print(f"✅ 학습 성공 → 모델: {model_name.upper()}, 레벨: {label_level}")
                success += 1
            except Exception as e:
                print(f"❌ 학습 실패 → 모델: {model_name.upper()}, 레벨: {label_level}")
                print(f"에러 내용: {e}")
                fail_log.append((model_name, label_level))
                fail += 1

        return success, fail, fail_log

    # 1차 학습
    print(f"\n🧠 총 학습 조합 수: {len(model_list) * len(level_list)}개")
    jobs = [(m, l) for m in model_list for l in level_list]
    total_success, total_fail, failed_jobs = run_jobs(jobs)

    retry_count = 0  # ✅ 에러 방지용 초기화
    if args.repeat_fail and failed_jobs:
        print(f"\n🔁 실패 조합 재시도 시작 (최대 {args.max_retry}회 반복)\n")
        while failed_jobs and retry_count < args.max_retry:
            retry_count += 1
            print(f"🔄 [재시도 {retry_count}/{args.max_retry}] {len(failed_jobs)}개 조합")
            success, fail, failed_jobs = run_jobs(failed_jobs)
            total_success += success
            total_fail = len(failed_jobs)  # 최신 실패만 반영

    # ✅ 최종 요약
    print("\n🎉 전체 학습 루프 종료!")
    total_attempts = len(jobs) + retry_count * len(jobs)  # 총 시도 수
    print(f"\n📊 최종 학습 요약: 총 시도 {total_attempts}회")
    print(f"✅ 최종 성공: {total_success}개")
    print(f"❌ 최종 실패: {total_fail}개 → 성공률: {total_success / (total_success + total_fail) * 100:.1f}%")

    if total_fail > 0:
        print("\n❌ 최종 실패 목록:")
        for model_name, label_level in failed_jobs:
            print(f"   - {model_name.upper()} - {label_level}")

if __name__ == "__main__":
    run()
