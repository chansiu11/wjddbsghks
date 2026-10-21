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
  a:["aa","visemeaa","mouthopen","jawopen"],i:["ih","visemeih","mouthi"],
  u:["ou","visemeou","mouthu"],e:["ee","visemeee","mouthe"],o:["oh","visemeoh","moutho"],
  joy:["happy","smile","joy"],browup:["browup","browraise"]
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
  // Preserve FBX/glTF rest rotations. Generated armatures typically use
  // non-identity bone rotations unlike the neutral VRM skeleton.
  for(const {bone} of bones){
    if(bone.quaternion?.clone){
      bone.userData=bone.userData||{};
      bone.userData.genericRestQuaternion=bone.quaternion.clone();
    }
  }
  const map=Object.create(null);
  for(const target of Object.keys(aliases)) map[normalize(target)]=findBone(bones,target);
  const missing=needs.filter(n=>!map[normalize(n)]);
  if(missing.length)throw Error("GLB 사람형 뼈대가 부족합니다: "+missing.join(", ")+". Blender에서 뼈대 이름을 설정하거나 VRM으로 변환하세요.");
  const hip=map.hips, head=map.head||map.neck||hip;
  scene.updateMatrixWorld(true);
  // AI mesh generators usually export a tiny, ground-centered object rather
  // than a VRM-sized human. Fit to ~1.7m and raise the soles above the floor.
  let bottom=Infinity,top=-Infinity;
  scene.traverse(node=>{
    if(!node.isMesh||!node.geometry||!node.matrixWorld)return;
    const geometry=node.geometry;
    if(!geometry.boundingBox) geometry.computeBoundingBox?.();
    const box=geometry.boundingBox?.clone();
    if(!box)return;
    box.applyMatrix4(node.matrixWorld);
    bottom=Math.min(bottom,box.min.y);
    top=Math.max(top,box.max.y);
  });
  const height=top-bottom;
  if(Number.isFinite(height) && height>0.02 && scene.scale && scene.position){
    const scale=Math.max(0.05,Math.min(30,1.7/height));
    scene.scale.multiplyScalar(scale);
    scene.updateMatrixWorld(true);
    let raisedBottom=Infinity;
    scene.traverse(node=>{
      if(!node.isMesh||!node.geometry?.boundingBox||!node.matrixWorld)return;
      const box=node.geometry.boundingBox.clone().applyMatrix4(node.matrixWorld);
      raisedBottom=Math.min(raisedBottom,box.min.y);
    });
    if(Number.isFinite(raisedBottom)){
      scene.position.y+=0.025-raisedBottom;
      scene.updateMatrixWorld(true);
    }
    scene.userData=scene.userData||{};
    scene.userData.genericAvatarFit={originalHeight:height,scale};
  }
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
  // Optional lightweight secondary motion for meshes with explicit hair / hem
  // helper joints. It is deliberately inert for ordinary rigs (including VRM)
  // and does not simulate the entire garment, which would require authored cloth.
  const springNames=[
    ["hair_spring",24,6.5,1.6],
    ["cloth_front_l",15,5.4,1.1],
    ["cloth_front_r",15,5.4,1.1]
  ];
  const springs=springNames.map(([name,stiffness,damping,inertia])=>{
    const bone=bones.find(entry=>entry.clean===normalize(name))?.bone;
    if(!bone||!bone.parent||!bone.quaternion)return null;
    // Read the world orientation of the moving ancestor, not the helper's
    // immediate local parent: Kalidoface rotates neck/spine while pelvis/head
    // may stay at their neutral *local* quaternion.
    const driver=name.startsWith("hair")
      ? (map[normalize("Neck")]||bone.parent)
      : (map[normalize("Chest")]||bone.parent);
    driver.updateWorldMatrix?.(true,false);
    const worldQ=driver.getWorldQuaternion?.(bone.quaternion.clone())||driver.quaternion.clone();
    return {bone,rest:bone.quaternion.clone(),driver,
      last:worldQ,vx:0,vz:0,angleX:0,angleZ:0,
      stiffness,damping,inertia};
  }).filter(Boolean);
  function stepSpringBones(delta){
    if(!springs.length||!Number.isFinite(delta))return;
    // Clamp elapsed time when the app is backgrounded to avoid exploding
    // spring integration, while preserving energy from small head movements.
    const dt=Math.max(0.001,Math.min(delta,1/30));
    for(const spring of springs){
      spring.driver.updateWorldMatrix?.(true,false);
      const q=spring.driver.getWorldQuaternion?.(spring.rest.clone())||spring.driver.quaternion.clone();
      const diff=q.clone().multiply(spring.last.clone().invert());
      spring.last.copy(q);
      // Quaternion shortest arc, converted to a modest velocity impulse.
      const sign=diff.w<0?-1:1;
      spring.vx-=Math.max(-0.16,Math.min(0.16,2*diff.x*sign))*spring.inertia;
      spring.vz-=Math.max(-0.16,Math.min(0.16,2*diff.z*sign))*spring.inertia;
      const ax=-spring.stiffness*spring.angleX-spring.damping*spring.vx;
      const az=-spring.stiffness*spring.angleZ-spring.damping*spring.vz;
      spring.vx+=ax*dt;
      spring.vz+=az*dt;
      spring.angleX=Math.max(-0.24,Math.min(0.24,spring.angleX+spring.vx*dt));
      spring.angleZ=Math.max(-0.20,Math.min(0.20,spring.angleZ+spring.vz*dt));
      const qSwing=spring.rest.clone();
      // Three.js quaternion method exists on every GLTFLoader Bone.
      const eulerLike=spring.rest.clone().set(
        Math.sin(spring.angleX/2),0,Math.sin(spring.angleZ/2),Math.cos(spring.angleX/2)*Math.cos(spring.angleZ/2)
      ).normalize();
      spring.bone.quaternion.copy(qSwing).multiply(eulerLike);
    }
  }
  const expressionInputs=Object.create(null);
  const setMorph=(name,value)=>{
    const items=expressions[name];
    if(!items)return;
    for(const {mesh,index} of items) mesh.morphTargetInfluences[index]=value;
  };
  const proxy={
    setValue(preset,value){
      const key=normalize(preset);
      const v=Math.max(0,Math.min(1,Number(value)||0));
      expressionInputs[key]=v;
      setMorph(key,v);
      // A real Meshy scan lacks dedicated lip topology for all phonemes.
      // Combine similar detected vowels rather than replacing a previous
      // nonzero mouth shape with the last zero-valued callback.
      if(/meshy/i.test(filename)&&expressions.a){
        setMorph("a",Math.min(1,Math.max(expressionInputs.a||0,
          .52*(expressionInputs.i||0),.40*(expressionInputs.u||0))));
        setMorph("o",Math.min(1,Math.max(expressionInputs.o||0,
          .78*(expressionInputs.u||0))));
        setMorph("e",Math.min(1,Math.max(expressionInputs.e||0,
          .72*(expressionInputs.i||0))));
      }
    },
    getValue(preset){
      return expressionInputs[normalize(preset)]||0;
    }
  };
  return {
    scene,
    meta:{title:filename.replace(/\.glb$/i,"")},
    isGenericGLB:true,
    isMeshyAvatar:/meshy/i.test(filename),
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
    update(delta){stepSpringBones(delta)},
    secondaryMotion:{bones:springs.map(s=>s.bone.name),type:"damped-helper-bone"},
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
