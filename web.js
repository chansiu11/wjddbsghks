import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js';
import { FilesetResolver, PoseLandmarker } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.20/vision_bundle.mjs';

const $ = s => document.querySelector(s);
const status = $('#status'), startButton = $('#start'), stopButton = $('#stop');
const video = $('#camera');
const canvas = $('#scene');
const metrics = $('#metrics');
const links = [[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],[23,25],[25,27],[24,26],[26,28],[27,31],[28,32],[0,11],[0,12]];
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0c1728);
const camera = new THREE.PerspectiveCamera(38, 1, .1, 30);
camera.position.set(0, .1, 4.4);
const renderer = new THREE.WebGLRenderer({canvas, antialias: false, powerPreference: 'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.4));
renderer.outputColorSpace = THREE.SRGBColorSpace;
scene.add(new THREE.HemisphereLight(0xbdefff, 0x26325e, 2.0));
const key = new THREE.DirectionalLight(0xffffff, 2.1); key.position.set(-2,3,4); scene.add(key);
const mat = new THREE.MeshStandardMaterial({color:0x38dcdf, roughness:.49, metalness:.12});
const jointMat = new THREE.MeshStandardMaterial({color:0xf1fdff, roughness:.4});
const cylinder = new THREE.CylinderGeometry(.055,.065,1,8);
const sphere = new THREE.SphereGeometry(.078,10,8);
const bones = links.map(() => { const mesh = new THREE.Mesh(cylinder, mat); scene.add(mesh); return mesh; });
const joints = Array.from({length:33},()=>{const mesh=new THREE.Mesh(sphere,jointMat);scene.add(mesh);return mesh;});
const head = new THREE.Mesh(new THREE.SphereGeometry(.17,16,12), new THREE.MeshStandardMaterial({color:0xaaf8f2,roughness:.54})); scene.add(head);
const floor = new THREE.GridHelper(4, 16, 0x325678, 0x24324b); floor.position.y=-1.25; scene.add(floor);
const target=Array.from({length:33},()=>new THREE.Vector3());
const smooth=Array.from({length:33},()=>new THREE.Vector3());
const up=new THREE.Vector3(0,1,0), diff=new THREE.Vector3();
let hasPose=false, task=null, stream=null, running=false, lastVideoTime=-1, lastInference=0, lastRender=performance.now(), fps=0, inferenceMs=0, lastMetric=0;
const initial={0:[0,.72,0],11:[-.27,.52,0],12:[.27,.52,0],13:[-.44,.21,0],14:[.44,.21,0],15:[-.54,-.03,0],16:[.54,-.03,0],23:[-.17,-.18,0],24:[.17,-.18,0],25:[-.19,-.58,0],26:[.19,-.58,0],27:[-.19,-1,0],28:[.19,-1,0],31:[-.2,-1.09,.12],32:[.2,-1.09,.12]};
for(const [k,p] of Object.entries(initial)) target[+k].set(...p);
for(let i=0;i<33;i++) smooth[i].copy(target[i]);
function resize(){
 const w=canvas.clientWidth,h=canvas.clientHeight;
 if(w && h && (canvas.width!==Math.round(w*renderer.getPixelRatio())||canvas.height!==Math.round(h*renderer.getPixelRatio()))){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
}
function draw(now){
 resize();
 for(let i=0;i<33;i++) smooth[i].lerp(target[i],hasPose?.28:.09);
 links.forEach(([a,b],i)=>{
   const p=smooth[a],q=smooth[b],mesh=bones[i];
   diff.subVectors(q,p); const length=diff.length();
   mesh.position.copy(p).add(q).multiplyScalar(.5);
   mesh.quaternion.setFromUnitVectors(up,diff.clone().normalize());
   mesh.scale.set(1,length,1);
   mesh.visible=length>.025;
 });
 const visible=new Set(links.flat());
 joints.forEach((m,i)=>{m.visible=visible.has(i);m.position.copy(smooth[i]);});
 head.position.copy(smooth[0]).add(new THREE.Vector3(0,.16,0));
 renderer.render(scene,camera);
 fps= fps*.9+1000/Math.max(1,now-lastRender)*.1; lastRender=now;
 if(now-lastMetric>800){ metrics.textContent=`화면 ${Math.round(fps)} FPS · 인식 ${Math.round(inferenceMs)} ms`; lastMetric=now; }
 if(running && task && video.readyState>=2 && video.currentTime!==lastVideoTime && now-lastInference>=40){
   lastVideoTime=video.currentTime; lastInference=now;
   try {
     const t=performance.now();
     const result=task.detectForVideo(video,now);
     inferenceMs=inferenceMs*.7+(performance.now()-t)*.3;
     const points=result.worldLandmarks?.[0];
     if(points?.length>=33){
       for(let i=0;i<33;i++){const p=points[i];target[i].set(-p.x*1.9,-p.y*1.9,-p.z*1.9);}
       hasPose=true;status.textContent='전신 인식 중';
     } else status.textContent='몸 전체가 카메라에 보이게 해주세요';
   }catch(e){status.textContent='인식 오류: '+e.message;stop();}
 }
 requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
async function loadModel(){
 const wasm='https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.20/wasm';
 const files=await FilesetResolver.forVisionTasks(wasm);
 const model='https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task';
 try {return await PoseLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:model,delegate:'GPU'},runningMode:'VIDEO',numPoses:1,outputSegmentationMasks:false});}
 catch(e){ console.warn('GPU unavailable; using CPU',e); return PoseLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:model,delegate:'CPU'},runningMode:'VIDEO',numPoses:1,outputSegmentationMasks:false});}
}
async function start(){
 startButton.disabled=true;status.textContent='카메라 연결 중…';
 try {
   stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:'user',width:{ideal:640},height:{ideal:480},frameRate:{ideal:30,max:30}}});
   video.srcObject=stream;await video.play();
   status.textContent='인식 모델 로딩 중… (첫 실행은 다운로드 필요)';
   task ??= await loadModel();
   running=true;stopButton.hidden=false;startButton.hidden=true;
   status.textContent='전신이 보이게 태블릿을 세워주세요';
 }catch(e){ stop();status.textContent=`시작 실패: ${e.message}`;startButton.disabled=false; }
}
function stop(){running=false;stream?.getTracks().forEach(track=>track.stop());stream=null;video.srcObject=null;startButton.disabled=false;startButton.hidden=false;stopButton.hidden=true;status.textContent='카메라가 꺼졌습니다';}
startButton.addEventListener('click',start);
stopButton.addEventListener('click',stop);
window.addEventListener('pagehide',()=>stream?.getTracks().forEach(t=>t.stop()));
