import { Composition, Still } from "remotion";

import { CowboyCut } from "./CowboyCut";
import { CowboyCutUser } from "./CowboyCutUser";
import { CowboyDuck } from "./CowboyDuck";
import { Duck } from "./Duck";
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
        id="ThinkScratch"
        component={ThinkScratch}
        durationInFrames={120}
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
      <Still id="DuckMain" component={Duck} width={1080} height={1080} defaultProps={{ expression: "main" }} />
      <Still id="DuckWink" component={Duck} width={1080} height={1080} defaultProps={{ expression: "wink" }} />
      <Still id="DuckHappy" component={Duck} width={1080} height={1080} defaultProps={{ expression: "happy" }} />
      <Still
        id="DuckCurious"
        component={Duck}
        width={1080}
        height={1080}
        defaultProps={{ expression: "curious" }}
      />
      <Still
        id="CowboyMain"
        component={CowboyDuck}
        width={1080}
        height={1080}
        defaultProps={{ pose: "main" }}
      />
      <Still
        id="CowboyWave"
        component={CowboyDuck}
        width={1080}
        height={1080}
        defaultProps={{ pose: "wave" }}
      />
      <Still id="CutRest" component={CowboyCut} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="CutWave" component={CowboyCut} width={1856} height={1280} defaultProps={{ pose: "wave" }} />
      <Still id="CutBlink" component={CowboyCut} width={1856} height={1280} defaultProps={{ pose: "blink" }} />
      <Still id="UserRest" component={CowboyCutUser} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="UserWave" component={CowboyCutUser} width={1856} height={1280} defaultProps={{ pose: "wave" }} />
      <Still id="UserBlink" component={CowboyCutUser} width={1856} height={1280} defaultProps={{ pose: "blink" }} />
      <Still id="UserDetach" component={CowboyCutUser} width={1856} height={1280} defaultProps={{ pose: "detach" }} />
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
      <Still id="HorseRest" component={HorseCut} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="HorseStep" component={HorseCut} width={1856} height={1280} defaultProps={{ pose: "step" }} />
      <Still id="RidingRest" component={RidingCut} width={1856} height={1280} defaultProps={{ pose: "rest" }} />
      <Still id="RidingRide" component={RidingCut} width={1856} height={1280} defaultProps={{ pose: "ride" }} />
      <Still
        id="RidingMark"
        component={RidingCut}
        width={1856}
        height={1280}
        defaultProps={{ pose: "rest", markAnchor: true }}
      />
    </>
  );
};
