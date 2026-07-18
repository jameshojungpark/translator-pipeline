import type { TextSize } from "../model/use-text-size";

import "./TextSizeControl.css";

const SIZES: { value: TextSize; label: string }[] = [
  { value: "small", label: "Small text" },
  { value: "medium", label: "Medium text" },
  { value: "large", label: "Large text" },
];

/** Segmented A/A/A control for the caption text size. */
export function TextSizeControl({
  value,
  onChange,
}: {
  value: TextSize;
  onChange: (size: TextSize) => void;
}) {
  return (
    <div className="text-size" role="group" aria-label="Text size">
      {SIZES.map((size) => (
        <button
          key={size.value}
          className={`text-size-btn ${size.value}${value === size.value ? " on" : ""}`}
          title={size.label}
          aria-pressed={value === size.value}
          onClick={() => onChange(size.value)}
        >
          A
        </button>
      ))}
    </div>
  );
}
