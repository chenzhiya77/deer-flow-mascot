import { AbsoluteFill } from "remotion";

export type DuckExpression = "main" | "wink" | "happy" | "curious";

const BODY = "#F5A63C";
const BODY_DARK = "#E8912F";
const CREAM = "#FFF4E2";
const BEAK = "#E8722F";
const BEAK_DARK = "#D9631F";
const NOSTRIL = "#C25A22";
const MOUTH = "#A83E14";
const INK = "#2B2B2B";
const SHADOW = "#F5E7CE";
const BLUSH = "#F0895A";

type DuckProps = {
  readonly expression: DuckExpression;
};

const Eye = ({ cx, cy }: { readonly cx: number; readonly cy: number }) => (
  <g>
    <ellipse cx={cx} cy={cy} rx={27} ry={33} fill={INK} />
    <circle cx={cx + 10} cy={cy - 14} r={8} fill="#FFFFFF" />
  </g>
);

const ClosedEye = ({
  x,
  y,
  up,
}: {
  readonly x: number;
  readonly y: number;
  readonly up: boolean;
}) => {
  const d = up
    ? `M ${x - 32} ${y + 12} Q ${x} ${y - 26} ${x + 32} ${y + 12}`
    : `M ${x - 32} ${y - 8} Q ${x} ${y + 24} ${x + 32} ${y - 8}`;
  return <path d={d} fill="none" stroke={INK} strokeWidth={17} strokeLinecap="round" />;
};

const Brow = ({ x, y, lift }: { readonly x: number; readonly y: number; readonly lift: number }) => (
  <path
    d={`M ${x - 42} ${y + 4 - lift} Q ${x} ${y - 20 - lift} ${x + 42} ${y + 4 - lift}`}
    fill="none"
    stroke={INK}
    strokeWidth={14}
    strokeLinecap="round"
  />
);

const Beak = ({ open }: { readonly open: number }) => {
  const diamond =
    "M 540 462 Q 618 478 635 505 Q 618 532 540 549 Q 462 532 445 505 Q 462 478 540 462 Z";
  const upper =
    "M 540 462 Q 618 478 635 505 Q 618 515 540 521 Q 462 515 445 505 Q 462 478 540 462 Z";
  const lower =
    "M 445 505 Q 462 532 540 549 Q 618 532 635 505 Q 618 497 540 493 Q 462 497 445 505 Z";
  return (
    <g>
      <path d={diamond} fill={MOUTH} />
      <path d={upper} fill={BEAK} />
      <ellipse cx={508} cy={489} rx={7} ry={5} fill={NOSTRIL} />
      <ellipse cx={572} cy={489} rx={7} ry={5} fill={NOSTRIL} />
      <path d={lower} fill={BEAK_DARK} transform={`translate(0 ${open})`} />
    </g>
  );
};

export const Duck = ({ expression }: DuckProps) => {
  const tilt = expression === "wink" ? -4 : expression === "curious" ? 7 : 0;
  const wingLift = expression === "happy" ? -26 : 0;
  const browLift = expression === "happy" ? 30 : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      <svg viewBox="0 0 1080 1080" width="100%" height="100%">
        <ellipse cx={540} cy={1002} rx={280} ry={26} fill={SHADOW} />
        <g transform={`rotate(${tilt} 540 700)`}>
          {/* feather tuft */}
          <ellipse cx={540} cy={185} rx={26} ry={68} fill={BODY} />
          <ellipse cx={502} cy={198} rx={22} ry={58} fill={BODY} transform="rotate(-22 502 245)" />
          <ellipse cx={578} cy={198} rx={22} ry={58} fill={BODY} transform="rotate(22 578 245)" />

          {/* head + body */}
          <ellipse cx={540} cy={745} rx={255} ry={235} fill={BODY} />
          <circle cx={540} cy={430} r={195} fill={BODY} />
          <ellipse cx={540} cy={815} rx={150} ry={120} fill={CREAM} />

          {/* blush */}
          <ellipse cx={395} cy={490} rx={42} ry={25} fill={BLUSH} opacity={0.5} />
          <ellipse cx={685} cy={490} rx={42} ry={25} fill={BLUSH} opacity={0.5} />

          {/* face */}
          {expression === "happy" ? (
            <>
              <ClosedEye x={470} y={425} up />
              <ClosedEye x={610} y={425} up />
            </>
          ) : expression === "wink" ? (
            <>
              <Eye cx={470} cy={425} />
              <ClosedEye x={610} y={425} up={false} />
            </>
          ) : (
            <>
              <Eye cx={expression === "curious" ? 460 : 470} cy={425} />
              <Eye cx={expression === "curious" ? 600 : 610} cy={425} />
            </>
          )}
          <Brow x={470} y={360} lift={browLift} />
          <Brow x={610} y={360} lift={expression === "curious" ? 30 : browLift} />

          <Beak open={expression === "happy" ? 22 : expression === "curious" ? 8 : 0} />

          {/* wings */}
          <ellipse
            cx={305}
            cy={745}
            rx={58}
            ry={100}
            fill={BODY_DARK}
            transform={`rotate(${20 + wingLift} 305 745)`}
          />
          <ellipse
            cx={775}
            cy={745}
            rx={58}
            ry={100}
            fill={BODY_DARK}
            transform={`rotate(${-20 - wingLift} 775 745)`}
          />

          {/* feet */}
          <rect
            x={405}
            y={938}
            width={128}
            height={58}
            rx={29}
            fill={BEAK}
            transform="rotate(-8 469 967)"
          />
          <rect
            x={547}
            y={938}
            width={128}
            height={58}
            rx={29}
            fill={BEAK}
            transform="rotate(8 611 967)"
          />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
