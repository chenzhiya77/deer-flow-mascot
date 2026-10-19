import { Composition, Still } from "remotion";

import { CowboyCutUser } from "./CowboyCutUser";
import { DuckFall } from "./DuckFall";
import { DuckJump } from "./DuckJump";
import { DuckWalk } from "./DuckWalk";
import { HorseCut } from "./HorseCut";
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
      <Still id="HorseRest" component={HorseCut} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="HorseStep" component={HorseCut} width={1856} height={1280} defaultProps={{ pose: "step" }} />
      <Still id="RidingRest" component={RidingCut} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="RidingRide" component={RidingCut} width={1856} height={1280} defaultProps={{ pose: "ride" }} />
    </>
  );
};
