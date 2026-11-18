export default function TabList({ items, value, onChange, label, id, className = "tabs" }) {
  const select = (index) => {
    onChange(items[index].value);
    document.getElementById(`${id}-tab-${items[index].value}`)?.focus();
  };
  return (
    <div className={className} role="tablist" aria-label={label}>
      {items.map((item, index) => (
        <button
          key={item.value}
          type="button"
          role="tab"
          id={`${id}-tab-${item.value}`}
          aria-selected={value === item.value}
          aria-controls={`${id}-panel-${item.value}`}
          tabIndex={value === item.value ? 0 : -1}
          onClick={() => onChange(item.value)}
          onKeyDown={(event) => {
            const positions = {
              ArrowRight: (index + 1) % items.length,
              ArrowLeft: (index + items.length - 1) % items.length,
              Home: 0,
              End: items.length - 1,
            };
            if (!(event.key in positions)) return;
            event.preventDefault();
            select(positions[event.key]);
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
