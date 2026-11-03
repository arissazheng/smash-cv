// Playable stages, in picker order.
//
// Owner: Person 4.
//
// `id` must be in STAGES in network/protocol.py and game/stage.py (a test
// checks); `image` is the stage art in assets/stages/.

export const STAGES = [
  { id: "memorial_glade", name: "Memorial Glade", blurb: "Floating island, three ledges" },
  { id: "gateway", name: "Gateway", blurb: "Wide floor, balconies at three heights" },
  { id: "sather_gate", name: "Sather Gate", blurb: "Fight on the pillars and the arch" },
  { id: "soda_hall", name: "Soda Hall", blurb: "Street, signal arm and arch sills" },
];

export function stageImage(id, assetBase = "/assets") {
  return `${assetBase}/stages/${id}.png`;
}
