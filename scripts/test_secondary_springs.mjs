import { createGenericGLBAvatar } from "../assets/glb-avatar-adapter.js";

class Quaternion {
  constructor(x=0,y=0,z=0,w=1){Object.assign(this,{x,y,z,w})}
  clone(){return new Quaternion(this.x,this.y,this.z,this.w)}
  copy(q){Object.assign(this,{x:q.x,y:q.y,z:q.z,w:q.w});return this}
  set(x,y,z,w){Object.assign(this,{x,y,z,w});return this}
  invert(){this.x*=-1;this.y*=-1;this.z*=-1;return this}
  multiply(b){
    const a=this.clone();
    return this.set(
      a.x*b.w+a.w*b.x+a.y*b.z-a.z*b.y,
      a.y*b.w+a.w*b.y+a.z*b.x-a.x*b.z,
      a.z*b.w+a.w*b.z+a.x*b.y-a.y*b.x,
      a.w*b.w-a.x*b.x-a.y*b.y-a.z*b.z
    );
  }
  normalize(){const n=Math.hypot(this.x,this.y,this.z,this.w)||1;return this.set(this.x/n,this.y/n,this.z/n,this.w/n)}
}
function bone(name,parent=null){
  const b={
    name,parent,isBone:true,position:{x:0,y:0,z:0},
    quaternion:new Quaternion(),userData:{},
    updateWorldMatrix(){},
    getWorldQuaternion(target){
      if(this.parent?.getWorldQuaternion)target.copy(this.parent.getWorldQuaternion(new Quaternion())).multiply(this.quaternion);
      else target.copy(this.quaternion);
      return target;
    }
  };return b;
}
const rig=[];
const pelvis=bone("pelvis");rig.push(pelvis);
const spine=bone("spine_01",pelvis),chest=bone("spine_02",spine),upperChest=bone("spine_03",chest);
const neck=bone("neck_01",upperChest),head=bone("head",neck);
rig.push(spine,chest,upperChest,neck,head);
for(const side of ["l","r"]){
  for(const name of ["clavicle","upperarm","lowerarm","hand","thigh","calf","foot"]){
    rig.push(bone(name+"_"+side,pelvis));
  }
}
const hair=bone("hair_spring",head),clothL=bone("cloth_front_l",pelvis),clothR=bone("cloth_front_r",pelvis);
rig.push(hair,clothL,clothR);
const scene={traverse(fn){rig.forEach(fn)},updateMatrixWorld(){}};
const avatar=createGenericGLBAvatar({scene},"meshy-rig-test.glb");
const springs=new Set(avatar.secondaryMotion.bones);
for(const name of ["hair_spring","cloth_front_l","cloth_front_r"]){
  if(!springs.has(name))throw Error("Missing simulated helper: "+name);
}
avatar.update(1/60);
neck.quaternion.set(.14,0,0,.99).normalize();
chest.quaternion.set(.10,0,0,.995).normalize();
for(let i=0;i<28;i++)avatar.update(1/60);
function springDelta(b){return Math.hypot(b.quaternion.x,b.quaternion.y,b.quaternion.z)}
const hairAngle=springDelta(hair),clothAngle=springDelta(clothL);
if(!(hairAngle>0.002))throw Error("Hair did not respond to rotated neck: "+hairAngle);
if(!(clothAngle>0.002))throw Error("Cloth did not respond to rotated chest: "+clothAngle);
for(const b of [hair,clothL,clothR])if(springDelta(b)>.26)throw Error("Unbounded spring "+b.name);
neck.quaternion.set(0,0,0,1);chest.quaternion.set(0,0,0,1);
for(let i=0;i<240;i++)avatar.update(1/60);
if(springDelta(hair)>.025||springDelta(clothL)>.025)throw Error("Spring failed to settle");
console.log("SPRING_TEST_PASSED",{springs:avatar.secondaryMotion.bones,hairAngle,clothAngle});
