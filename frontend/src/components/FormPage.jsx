import "../auth.css";

export default function FormPage({ title, children, wide = false, navigation }) {
  return (
    <div className={`container auth-page${wide ? " form-page-wide" : ""}`}>
      <section className="auth-content form-sheet">
        {navigation}
        <h1>{title}</h1>
        {children}
      </section>
    </div>
  );
}
