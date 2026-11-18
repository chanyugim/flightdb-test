import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { requestApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { formatKst } from "../utils/format";
import Icon from "../components/Icon";
import LoadingFlight from "../components/LoadingFlight";
import "../benefits.css";

export default function Benefits() {
  const { member, isLoggedIn } = useAuth();
  const { hash } = useLocation();
  const [grades, setGrades] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setErrors({});
    Promise.allSettled([
      requestApi("/grades", { signal: controller.signal }),
      requestApi("/promotions", { signal: controller.signal }),
    ]).then(([gradeResult, promotionResult]) => {
      if (controller.signal.aborted) return;
      setGrades(gradeResult.status === "fulfilled" ? gradeResult.value : []);
      setPromotions(promotionResult.status === "fulfilled" ? promotionResult.value : []);
      setErrors({
        grades: gradeResult.status === "rejected" ? gradeResult.reason.message : "",
        promotions: promotionResult.status === "rejected" ? promotionResult.reason.message : "",
      });
      setLoading(false);
    });
    return () => controller.abort();
  }, [reload]);

  useEffect(() => {
    if (!loading && hash) document.getElementById(hash.slice(1))?.scrollIntoView({ block: "start" });
  }, [loading, hash]);

  const currentGrade = grades.find((grade) => grade.grade_code === member?.grade_code);
  const errorNotice = (message) => (
    <div className="benefits-notice" role="alert">
      <p>{message}</p>
      <button onClick={() => setReload((value) => value + 1)}>다시 불러오기</button>
    </div>
  );

  return (
    <div className="container page benefits-page">
      <header className="benefits-hero">
        <div>
          <span className="benefits-eyebrow">회원 혜택</span>
          <h1>여행에 더하는 혜택</h1>
          <p>등급별 포인트 적립부터<br />지금 이용할 수 있는 프로모션까지.</p>
          <nav aria-label="혜택 바로가기">
            <a href="#grades">등급별 혜택 ↓</a>
            <a href="#promotions">프로모션 ↓</a>
          </nav>
        </div>
      </header>

      <section className="benefits-member" aria-label="내 혜택">
        <Icon name="plane" />
        <div>
          <h2>{member ? `${member.name}님의 ${member.grade_name} 혜택` : "회원으로 더 알뜰한 여행"}</h2>
          <p>{member
            ? `보유 포인트 ${Number(member.point_balance).toLocaleString("ko-KR")}P${currentGrade ? ` · 결제 금액의 ${Number(currentGrade.point_rate)}% 적립` : ""}`
            : isLoggedIn ? "회원 정보를 확인하고 있어요." : "로그인하면 내 등급과 포인트를 확인하고 프로모션을 이용할 수 있어요."}</p>
        </div>
        <Link className="btn" to={isLoggedIn ? "/mypage" : "/login"}>{isLoggedIn ? "마이페이지" : "로그인"} →</Link>
      </section>

      {loading ? <LoadingFlight label="회원 혜택을 확인하고 있어요" /> : <>
        <section id="grades" className="benefits-section" aria-labelledby="grades-title">
          <div className="benefits-heading"><h2 id="grades-title">등급별 혜택</h2><p>회원 등급에 따라 포인트 적립률이 달라져요.</p></div>
          {errors.grades ? errorNotice(errors.grades) : !grades.length ? <p className="benefits-notice">현재 안내 가능한 회원 등급이 없어요.</p> :
            <div className="benefits-grades">
              {grades.map((grade) => <article key={grade.grade_code} className={`benefits-grade ${grade.grade_code === member?.grade_code ? "is-current" : ""}`}>
                <span className={`grade-emblem grade-${grade.grade_code.toLowerCase()}`} aria-hidden="true"><Icon name="plane" /></span>
                <h3>{grade.grade_name}{grade.grade_code === member?.grade_code && <span className="badge">내 등급</span>}</h3>
                <p className="grade-rate">{Number(grade.point_rate)}<span>%</span></p>
                <p>포인트 적립</p>
                <small>할인·포인트 사용 후 결제 금액 기준</small>
              </article>)}
            </div>}
          <p className="small muted">등급 혜택은 포인트 적립으로 제공돼요. 프로모션 할인은 아래에서 별도로 확인해 주세요.</p>
        </section>

        <section id="promotions" className="benefits-section" aria-labelledby="promotions-title">
          <div className="benefits-heading"><h2 id="promotions-title">진행 중인 프로모션</h2><p>예약할 때 원하는 프로모션 한 개를 선택해 주세요.</p></div>
          {errors.promotions ? errorNotice(errors.promotions) : !promotions.length ? <div className="benefits-notice"><h3>새로운 혜택을 준비하고 있어요</h3><p>현재 진행 중인 프로모션이 없어요. 회원 등급별 포인트 적립은 이용할 수 있어요.</p></div> :
            <div className="benefits-promotions">{promotions.map((promotion) => (
              <article className="benefit-promotion" id={`promotion-${promotion.promotion_id}`} key={promotion.promotion_id}>
                <div className="promotion-discount"><span>회원 전용</span><strong>{Number(promotion.discount_rate)}<small>%</small></strong><span>기본 운임 할인</span></div>
                <div className="promotion-description">
                  <h3>{promotion.promotion_name}</h3>
                  <dl><dt>예약 적용 기간 · 한국 시간</dt><dd>{formatKst(promotion.start_at)}<br />~ {formatKst(promotion.end_at)}</dd></dl>
                  <p>탑승일이 아닌 예약 시점 기준이에요.</p>
                  <Link to="/">항공편 찾아보기 →</Link>
                </div>
              </article>
            ))}</div>}
        </section>
      </>}

      <section className="benefits-guide" aria-labelledby="benefits-guide-title">
        <h2 id="benefits-guide-title">혜택 이용 안내</h2>
        <ul>
          <li>프로모션 할인·포인트 사용 및 적립은 로그인한 회원에게 제공돼요.</li>
          <li>예약 한 건에 프로모션 한 개를 선택할 수 있으며, 여러 프로모션을 합산할 수 없어요.</li>
          <li>프로모션 할인 후 보유 포인트를 사용할 수 있고, 최종 결제 금액에 등급별 적립률이 적용돼요.</li>
          <li>예약 취소 시 사용한 포인트는 반환되고, 해당 예약으로 적립된 포인트는 회수돼요.</li>
          <li>최종 적용 금액은 예약 화면에서 확인해 주세요.</li>
        </ul>
      </section>
      <p className="benefits-credit">배경 출처: <a href="https://unsplash.com/photos/ifHBo0TTuBI" target="_blank" rel="noreferrer">Joshua Tsu / Unsplash</a></p>
    </div>
  );
}
