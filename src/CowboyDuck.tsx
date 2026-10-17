import { AbsoluteFill } from "remotion";

const BODY = "#F3D28E";
const BODY_DARK = "#E9C27C";
const BEAK = "#F2A863";
const BEAK_DARK = "#E08B45";
const NOSTRIL = "#C97B3C";
const HAT = "#DCC7A6";
const HAT_UNDER = "#BFA27C";
const BAND = "#6B5540";
const BELT = "#4A3826";
const BUCKLE = "#C9C9CE";
const LEG = "#F0A45E";
const BOOT = "#E8944B";
const BOLT = "#F5C542";
const INK = "#3A2E22";
const EYE = "#22201E";
const SHADOW = "#EFE6D2";

type CowboyDuckProps = {
  readonly pose: "main" | "wave";
};

const Hand = ({ x, y }: { readonly x: number; readonly y: number }) => (
  <circle cx={x} cy={y} r={64} fill={BODY} stroke={INK} strokeWidth={7} />
);

const Boot = ({
  x,
  flip,
}: {
  readonly x: number;
  readonly flip: boolean;
}) => (
  <g transform={`rotate(${flip ? 4 : -4} ${x + 75} 999)`}>
    <rect x={x + 64} y={905} width={58} height={86} rx={12} fill={LEG} stroke={INK} strokeWidth={6} />
    <rect x={x} y={972} width={150} height={56} rx={16} fill={BOOT} stroke={INK} strokeWidth={6} />
  </g>
);

const Hat = () => (
  <g transform="rotate(-8 540 300)">
    <ellipse cx={540} cy={352} rx={398} ry={72} fill={HAT_UNDER} stroke={INK} strokeWidth={7} />
    <ellipse cx={540} cy={330} rx={398} ry={74} fill={HAT} stroke={INK} strokeWidth={7} />
    <path
      d="M 418 336 Q 424 178 540 162 Q 656 178 662 336 Z"
      fill={HAT}
      stroke={INK}
      strokeWidth={7}
      strokeLinejoin="round"
    />
    <rect x={416} y={296} width={248} height={46} rx={10} fill={BAND} stroke={INK} strokeWidth={6} />
  </g>
);

const Bolt = () => (
  <path
    d="M 648 338 L 712 338 L 672 392 L 716 392 L 636 470 L 664 404 L 622 404 Z"
    fill={BOLT}
    stroke={INK}
    strokeWidth={5}
    strokeLinejoin="round"
  />
);

const Face = () => (
  <g>
    <rect x={428} y={495} width={44} height={88} rx={12} fill={EYE} />
    <rect x={608} y={495} width={44} height={88} rx={12} fill={EYE} />
    <circle cx={443} cy={515} r={9} fill="#FFFFFF" />
    <circle cx={623} cy={515} r={9} fill="#FFFFFF" />
    <path
      d="M 420 648 Q 420 622 540 614 Q 660 622 660 648 Q 660 672 540 678 Q 420 672 420 648 Z"
      fill={BEAK}
      stroke={INK}
      strokeWidth={6}
      strokeLinejoin="round"
    />
    <ellipse cx={508} cy={638} rx={8} ry={5} fill={NOSTRIL} />
    <ellipse cx={572} cy={638} rx={8} ry={5} fill={NOSTRIL} />
    <path
      d="M 452 690 Q 540 706 628 690 Q 622 722 540 728 Q 458 722 452 690 Z"
      fill={BEAK_DARK}
      stroke={INK}
      strokeWidth={6}
      strokeLinejoin="round"
    />
  </g>
);

const Belt = () => (
  <g>
    <rect x={314} y={798} width={462} height={44} rx={10} fill={BELT} />
    <rect x={502} y={790} width={76} height={60} rx={10} fill={BUCKLE} stroke={INK} strokeWidth={5} />
    <rect x={521} y={806} width={38} height={28} rx={6} fill={BELT} />
  </g>
);

export const CowboyDuck = ({ pose }: CowboyDuckProps) => {
  const tilt = pose === "wave" ? -3 : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      <svg viewBox="0 0 1080 1080" width="100%" height="100%">
        <ellipse cx={540} cy={1042} rx={290} ry={22} fill={SHADOW} />
        <g transform={`rotate(${tilt} 540 700)`}>
          <rect x={695} y={300} width={75} height={630} rx={33} fill={BODY_DARK} stroke={INK} strokeWidth={7} />
          <rect x={320} y={300} width={400} height={630} rx={55} fill={BODY} stroke={INK} strokeWidth={7} />
          <ellipse cx={540} cy={372} rx={300} ry={34} fill={INK} opacity={0.12} />
          <Bolt />
          <Hat />
          <Face />
          <Belt />
          <Boot x={388} flip={false} />
          <Boot x={542} flip />
          <Hand x={225} y={800} />
          <Hand x={855} y={pose === "wave" ? 600 : 800} />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
