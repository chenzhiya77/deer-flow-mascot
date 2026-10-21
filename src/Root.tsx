import { Composition, Still } from "remotion";

import { Bandana } from "./Bandana";
import { BEAK_STILL_H, BEAK_STILL_W } from "./beak-manifest";
import { Beak } from "./Beak";
import { CowboyCutUser } from "./CowboyCutUser";
import { CactusBelt } from "./CactusBelt";
import { DuckFall } from "./DuckFall";
import { DuckJump } from "./DuckJump";
import { DuckWalk } from "./DuckWalk";
import { HorseCut } from "./HorseCut";
import { HorseHead } from "./HorseHead";
import { MountUp } from "./MountUp";
import { RidingCut } from "./RidingCut";
import { ThinkScratch } from "./ThinkScratch";
import { WalkVideo } from "./WalkVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="WalkVideo"
        component={WalkVideo}
        durationInFrames={60}
        fps={30}
        width={1856}
        height={1280}
      />
      <Composition
        id="DuckWalk"
        component={DuckWalk}
        durationInFrames={60}
        fps={30}
        width={1856}
        height={1280}
      />
      <Composition
        id="DuckRun"
        component={DuckWalk}
        durationInFrames={60}
        fps={30}
        width={1856}
        height={1280}
        defaultProps={{ gait: "run" }}
      />
      <Composition
        id="DuckJump"
        component={DuckJump}
        durationInFrames={60}
        fps={30}
        width={1856}
        height={1280}
      />
      <Composition
        id="DuckFall"
        component={DuckFall}
        durationInFrames={120}
        fps={30}
        width={1856}
        height={1280}
      />
      <Composition
        id="MountUp"
        component={MountUp}
        durationInFrames={90}
        fps={30}
        width={1856}
        height={1280}
      />
      <Composition
        id="ThinkScratchV2"
        component={ThinkScratch}
        durationInFrames={192}
        fps={30}
        width={1856}
        height={1280}
        defaultProps={{
          shift: 72,
          steps: [
            [0, "normal"],
            [12, "wuyu"],
            [48, "zhuangsha"],
            [182, "normal"],
          ],
        }}
      />
      <Still id="UserRest" component={CowboyCutUser} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="UserWave" component={CowboyCutUser} width={1856} height={1280} defaultProps={{ pose: "wave" }} />
      <Still id="UserBlink" component={CowboyCutUser} width={1856} height={1280} defaultProps={{ pose: "blink" }} />
      <Still
        id="UserWuyu"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "wuyu" }}
      />
      <Still
        id="UserZhuangsha"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "zhuangsha" }}
      />
      <Still
        id="UserMiyanxiao"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "miyanxiao" }}
      />
      <Still
        id="UserHengmiyanxiao"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "hengmiyanxiao" }}
      />
      <Still
        id="UserRenzheng"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "renzheng" }}
      />
      <Still
        id="UserDaimeng"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "daimeng" }}
      />
      <Still
        id="UserXiakan"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "xiakan" }}
      />
      <Still
        id="UserYanbai"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", eyes: "yanbai" }}
      />
      <Still
        id="UserCactusBelt"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", belt: "cactus" }}
      />
      <Still
        id="UserBandana"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", belt: "cactus", bandana: true }}
      />
      <Still
        id="UserMouth"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", mouth: "split" }}
      />
      <Still
        id="FinalDuck"
        component={CowboyCutUser}
        width={1856}
        height={1280}
        defaultProps={{
          pose: "rest",
          belt: "cactus",
          bandana: true,
          mouth: "split",
          background: "transparent",
        }}
      />
      <Still id="HorseRest" component={HorseCut} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="HorseStep" component={HorseCut} width={1856} height={1280} defaultProps={{ pose: "step" }} />
      <Still id="RidingRest" component={RidingCut} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="RidingRide" component={RidingCut} width={1856} height={1280} defaultProps={{ pose: "ride" }} />
      <Still id="HorseHead" component={HorseHead} width={320} height={431} />
      <Still id="Beak" component={Beak} width={BEAK_STILL_W} height={BEAK_STILL_H} />
      <Still id="CactusBelt" component={CactusBelt} width={760} height={181} />
      <Still id="Bandana" component={Bandana} width={2120} height={724} />
    </>
  );
};
