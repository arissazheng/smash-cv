// Playable characters, in roster order.
//
// Owner: Person 4.
//
// `id` is the folder in assets/characters/ and must be in CHARACTERS in
// network/protocol.py (a test checks they match).

export const CHARACTERS = [
  { id: "efros", title: "Prof.", name: "Alyosha Efros" },
  { id: "ng", title: "Prof.", name: "Ren Ng" },
  { id: "liu", title: "Dean", name: "Tsu-Jae King Liu" },
  { id: "lyons", title: "Chancellor", name: "Rich Lyons" },
  { id: "oski", title: "Cal mascot", name: "Oski the Bear" },
];

export function portrait(id, assetBase = "/assets") {
  return `${assetBase}/characters/${id}/views/front.png`;
}
