// Generic GLB humanoid adapter for locally supplied, appropriately licensed 3D avatars.
// This does not embed, extract, fetch, or redistribute any third-party game assets.
// Supported: single-file .glb with a skinned humanoid armature (Mixamo and common bone names).
// Note: generic GLB rigs lack VRM standardized rotations, eye look-at, and expressions.
const normalize = (s) => String(s || "")
  .toLowerCase().replace(/mixamorig\d*/g,"").replace(/armature/g,"")
  .replace(/bip0*1/g,"").replace(/[^a-z0-9]/g,"");

const aliases = {
  Hips:["hips","pelvis","hip","root"],
  Spine:["spine","spine1","spine01","lowerback"],
  Chest:["chest","spine2","spine02","upperback"],
  UpperChest:["upperchest","spine3","spine03"],
  Neck:["neck","neck1","neck01"],
  Head:["head","head1"],
};
for (const side of ["Left","Right"]) {
  const s=side.toLowerCase(), short=s[0]; // Supports Mixamo and afk-rig ("_l" / "_r") suffix naming.
  Object.assign(aliases, {
    [side+"Shoulder"]:[s+"shoulder",s+"clavicle",short+"clavicle","clavicle"+short],
    [side+"UpperArm"]:[s+"upperarm",s+"arm",s+"uparm",short+"upperarm",short+"arm","upperarm"+short,"arm"+short],
    [side+"LowerArm"]:[s+"lowerarm",s+"forearm",s+"elbow",short+"forearm",short+"lowerarm","lowerarm"+short,"forearm"+short],
    [side+"Hand"]:[s+"hand",s+"wrist",short+"hand","hand"+short],
    [side+"UpperLeg"]:[s+"upperleg",s+"upleg",s+"thigh",short+"thigh",short+"upperleg","thigh"+short],
    [side+"LowerLeg"]:[s+"lowerleg",s+"leg",s+"calf",s+"shin",short+"calf","calf"+short,"shin"+short],
    [side+"Foot"]:[s+"foot",s+"ankle",short+"foot","foot"+short],
    [side+"Toes"]:[s+"toe",s+"toebase",short+"toe","ball"+short],
  });
  for(const digit of ["Thumb","Index","Middle","Ring","Little"]) {
    const id=digit.toLowerCase();
    for(const [part,number] of [["Proximal","1"],["Intermediate","2"],["Distal","3"]]) {
      aliases[side+digit+part] = [
        s+id+part.toLowerCase(),s+"hand"+id+number,s+id+number,id+"0"+number+short,id+number+short,
        short+id+number,s+"hand"+id+part.toLowerCase()
      ];
      if(digit==="Little") aliases[side+digit+part].push(s+"pinky"+number,s+"handpinky"+number,"pinky0"+number+short,"pinky"+number+short);
    }
  }
}
const needs=[
  "Hips","LeftUpperArm","LeftLowerArm","LeftHand","RightUpperArm","RightLowerArm",
  "RightHand","LeftUpperLeg","LeftLowerLeg","LeftFoot","RightUpperLeg",
  "RightLowerLeg","RightFoot"
];
const expressionAliases={
  blink:["blink","eyeblink"],blinkl:["blinkleft","eyeblinkleft","eyeblinkl"],
  blinkr:["blinkright","eyeblinkright","eyeblinkr"],
  a:["aa","visemeaa","mouthopen","jawopen"],i:["ih","visemeih"],
  u:["ou","visemeou"],e:["ee","visemeee"],o:["oh","visemeoh"],
  joy:["happy","smile","joy"]
};
function findBone(entries,target){
  const keys=aliases[target]||[target.toLowerCase()];
  for(const key of keys){
    const direct=entries.find(item=>item.clean===key);
    if(direct)return direct.bone;
  }
  for(const key of keys){
    // Exporters prepend e.g. Character_ or skeleton container names.
    const suffix=entries.find(item=>item.clean.endsWith(key));
    if(suffix)return suffix.bone;
  }
  return null;
}
export function createGenericGLBAvatar(gltf, filename="Character.glb") {
  const scene=gltf?.scene;
  if(!scene)throw Error("3D model scene not found");
  const bones=[], morphMeshes=[];
  scene.traverse(node=>{
    if(node.isBone) bones.push({bone:node,clean:normalize(node.name)});
    if(node.isMesh&&node.morphTargetDictionary&&node.morphTargetInfluences) morphMeshes.push(node);
  });
  if(!bones.length)throw Error("이 GLB에는 애니메이션 뼈대가 없습니다. 사람형 리깅 GLB/VRM 파일이 필요합니다.");
  const map=Object.create(null);
  for(const target of Object.keys(aliases)) map[normalize(target)]=findBone(bones,target);
  const missing=needs.filter(n=>!map[normalize(n)]);
  if(missing.length)throw Error("GLB 사람형 뼈대가 부족합니다: "+missing.join(", ")+". Blender에서 뼈대 이름을 설정하거나 VRM으로 변환하세요.");
  const hip=map.hips, head=map.head||map.neck||hip;
  scene.updateMatrixWorld(true);
  const expressions={};
  for(const mesh of morphMeshes){
    for(const [key,index] of Object.entries(mesh.morphTargetDictionary)){
      const k=normalize(key);
      for(const [preset,names] of Object.entries(expressionAliases)){
        if(names.includes(k)||(preset==="blink"&&k==="eyeclose")){
          (expressions[preset]??=[]).push({mesh,index});
        }
      }
    }
  }
  const proxy={
    setValue(preset,value){
      const items=expressions[normalize(preset)];
      if(!items)return;
      const v=Math.max(0,Math.min(1,Number(value)||0));
      for(const {mesh,index} of items) mesh.morphTargetInfluences[index]=v;
    }
  };
  return {
    scene,
    meta:{title:filename.replace(/\.glb$/i,"")},
    isGenericGLB:true,
    humanoid:{
      getBoneNode(name){return map[normalize(name)]||null},
      restPose:{hips:{position:[hip.position.x,hip.position.y,hip.position.z]}}
    },
    blendShapeProxy:proxy,
    lookAt:{applyer:{lookAt(){}}},
    firstPerson:{
      firstPersonBone:head,
      firstPersonOnlyLayer:9,
      thirdPersonOnlyLayer:10,
      setup({firstPersonOnlyLayer=9,thirdPersonOnlyLayer=10}={}){
        this.firstPersonOnlyLayer=firstPersonOnlyLayer;
        this.thirdPersonOnlyLayer=thirdPersonOnlyLayer;
      }
    },
    update(){},
    dispose(){
      scene.traverse(node=>{
        if(!node.isMesh)return;
        if(node.geometry?.dispose)node.geometry.dispose();
        const materials=Array.isArray(node.material)?node.material:[node.material];
        for(const m of materials){if(m?.dispose)m.dispose()}
      });
    }
  };
}
