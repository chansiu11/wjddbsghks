import { readFileSync } from "node:fs";
import { createGenericGLBAvatar } from "../assets/glb-avatar-adapter.js";

const path = process.argv[2];
if (!path) throw new Error("Usage: node validate_glb_adapter.mjs model.glb");
const bytes=readFileSync(path);
if (bytes.toString("ascii",0,4) !== "glTF")throw new Error("Not GLB");
const len=bytes.readUInt32LE(12);
const data=JSON.parse(bytes.subarray(20,20+len).toString("utf8"));
const skins=data.skins||[];
if(skins.length===0)throw new Error("No skin");
const jointIds=new Set(skins.flatMap(x=>x.joints));
const boneNames=[...jointIds].map(i=>data.nodes?.[i]?.name).filter(Boolean);
console.log("SKIN_JOINTS",jointIds.size);
console.log("BONE_NAMES",JSON.stringify(boneNames));
const bones=boneNames.map(name=>({isBone:true,name,position:{x:0,y:0,z:0}}));
const scene={traverse(fn){bones.forEach(fn)},updateMatrixWorld(){}};
const adapter=createGenericGLBAvatar({scene},"model.glb");
const required=[
  "Hips","Spine","Chest","Neck","Head",
  ...["Left","Right"].flatMap(side=>[
    "Shoulder","UpperArm","LowerArm","Hand","UpperLeg","LowerLeg","Foot",
    ...["Index","Thumb","Middle","Ring","Little"].flatMap(finger=>["Proximal","Intermediate","Distal"].map(part=>finger+part))
  ].map(part=>side+part))
];
const missing=required.filter(name=>!adapter.humanoid.getBoneNode(name));
console.log("RETARGETED",required.length-missing.length,"/",required.length,"MISSING",JSON.stringify(missing));
if(missing.length)process.exitCode=1;
