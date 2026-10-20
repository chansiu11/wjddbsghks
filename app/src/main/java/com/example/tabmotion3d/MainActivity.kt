package com.example.tabmotion3d

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.os.SystemClock
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarkerResult
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.max

class MainActivity : ComponentActivity() {
    private val worker = Executors.newSingleThreadExecutor()
    private val busy = AtomicBoolean(false)
    private var landmarker: PoseLandmarker? = null
    private lateinit var figure: FigureView
    private lateinit var status: TextView
    private var lastSubmitted = 0L
    private val permission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { allowed ->
        if (allowed) startCamera(cameraPreview) else status.text = "카메라 권한이 필요합니다"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = FrameLayout(this)
        val preview = PreviewView(this).apply { scaleType = PreviewView.ScaleType.FIT_CENTER; alpha = 0.18f }
        figure = FigureView(this)
        status = TextView(this).apply { text = "인식 준비 중"; textSize = 16f; setTextColor(0xffffffff.toInt()); setPadding(24, 24, 24, 24) }
        root.setBackgroundColor(0xff101726.toInt())
        root.addView(preview, FrameLayout.LayoutParams(-1, -1))
        root.addView(figure, FrameLayout.LayoutParams(-1, -1))
        root.addView(status, FrameLayout.LayoutParams(-1, -2, Gravity.TOP))
        setContentView(root)
        cameraPreview = preview
        worker.execute {
            try {
                landmarker = createLandmarker(true)
            } catch (_: Exception) {
                try { landmarker = createLandmarker(false) }
                catch (e: Exception) { runOnUiThread { status.text = "인식 모델 시작 실패: ${e.message}" }; return@execute }
            }
            runOnUiThread {
                status.text = "카메라 준비 중"
                if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) startCamera(preview)
                else permission.launch(Manifest.permission.CAMERA)
            }
        }
    }
    private lateinit var cameraPreview: PreviewView
    private fun createLandmarker(gpu: Boolean): PoseLandmarker {
        val base = BaseOptions.builder().setModelAssetPath("pose_landmarker_lite.task")
        if (gpu) base.setDelegate(Delegate.GPU)
        return PoseLandmarker.createFromOptions(this,
            PoseLandmarker.PoseLandmarkerOptions.builder()
                .setBaseOptions(base.build()).setRunningMode(RunningMode.LIVE_STREAM).setNumPoses(1)
                .setResultListener { result, _ -> onPose(result) }
                .setErrorListener { error -> runOnUiThread { status.text = "인식 오류: ${error.message}" }; busy.set(false) }
                .build())
    }
    private fun onPose(result: PoseLandmarkerResult) {
        val points = result.worldLandmarks().firstOrNull()
        if (points != null && points.size >= 33) {
            val xyz = FloatArray(33 * 3)
            points.forEachIndexed { i, p ->
                xyz[i * 3] = -p.x()
                xyz[i * 3 + 1] = -p.y()
                xyz[i * 3 + 2] = -p.z()
            }
            figure.setPose(xyz)
            runOnUiThread { status.text = "전신 인식 중 · 3D" }
        } else runOnUiThread { status.text = "카메라에 전신이 보이게 해주세요" }
        busy.set(false)
    }
    private fun startCamera(preview: PreviewView = cameraPreview) {
        val future = ProcessCameraProvider.getInstance(this)
        future.addListener({
            val provider = future.get()
            val imagePreview = Preview.Builder().build().also { it.surfaceProvider = preview.surfaceProvider }
            val analysis = ImageAnalysis.Builder()
                .setTargetResolution(android.util.Size(640, 480))
                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST).build()
            analysis.setAnalyzer(worker) { image ->
                val now = SystemClock.uptimeMillis()
                if (now - lastSubmitted < 33 || !busy.compareAndSet(false, true)) { image.close(); return@setAnalyzer }
                lastSubmitted = now
                try {
                    val buffer = image.planes[0].buffer
                    val bitmap = Bitmap.createBitmap(image.width, image.height, Bitmap.Config.ARGB_8888)
                    buffer.rewind(); bitmap.copyPixelsFromBuffer(buffer)
                    val matrix = Matrix().apply { postRotate(image.imageInfo.rotationDegrees.toFloat()); postScale(-1f, 1f) }
                    val rotated = Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
                    landmarker?.detectAsync(BitmapImageBuilder(rotated).build(), now) ?: busy.set(false)
                } catch (e: Exception) { busy.set(false); runOnUiThread { status.text = "카메라 처리 오류: ${e.message}" } }
                finally { image.close() }
            }
            provider.unbindAll()
            provider.bindToLifecycle(this, CameraSelector.DEFAULT_FRONT_CAMERA, imagePreview, analysis)
        }, ContextCompat.getMainExecutor(this))
    }
    override fun onDestroy() {
        super.onDestroy()
        worker.execute { landmarker?.close() }
        worker.shutdown()
    }
}

private class FigureView(context: android.content.Context) : GLSurfaceView(context) {
    private val figure = FigureRenderer()
    init { setEGLContextClientVersion(2); setRenderer(figure); renderMode = RENDERMODE_CONTINUOUSLY; setZOrderOnTop(true); holder.setFormat(android.graphics.PixelFormat.TRANSLUCENT) }
    fun setPose(xyz: FloatArray) = figure.setPose(xyz)
}

private class FigureRenderer : GLSurfaceView.Renderer {
    @Volatile private var target: FloatArray? = null
    private val smooth = FloatArray(99)
    private var initialized = false
    private var program = 0
    private var position = 0
    private val bones = intArrayOf(11,12, 11,13, 13,15, 12,14, 14,16, 11,23, 12,24, 23,24, 23,25, 25,27, 24,26, 26,28, 27,29, 29,31, 28,30, 30,32, 0,11, 0,12)
    private val vertex = "attribute vec3 a; uniform mat4 m; void main(){gl_Position=m*vec4(a,1.0); gl_PointSize=9.0;}"
    private val fragment = "precision mediump float; void main(){gl_FragColor=vec4(0.22,0.93,0.84,1.0);}"
    private val matrix = FloatArray(16)
    fun setPose(p: FloatArray) { target = p }
    override fun onSurfaceCreated(gl: javax.microedition.khronos.opengles.GL10?, config: javax.microedition.khronos.egl.EGLConfig?) {
        fun compile(type: Int, src: String): Int = GLES20.glCreateShader(type).also { GLES20.glShaderSource(it, src); GLES20.glCompileShader(it) }
        program = GLES20.glCreateProgram().also { GLES20.glAttachShader(it, compile(GLES20.GL_VERTEX_SHADER, vertex)); GLES20.glAttachShader(it, compile(GLES20.GL_FRAGMENT_SHADER, fragment)); GLES20.glLinkProgram(it) }
        position = GLES20.glGetAttribLocation(program, "a")
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        GLES20.glClearColor(0f, 0f, 0f, 0f)
    }
    override fun onSurfaceChanged(gl: javax.microedition.khronos.opengles.GL10?, width: Int, height: Int) {
        GLES20.glViewport(0, 0, width, height)
        android.opengl.Matrix.perspectiveM(matrix, 0, 42f, width.toFloat() / max(1, height), 0.1f, 10f)
        val view = FloatArray(16)
        android.opengl.Matrix.setLookAtM(view, 0, 0f, 0f, 3.5f, 0f, 0f, 0f, 0f, 1f, 0f)
        val projection = matrix.copyOf()
        android.opengl.Matrix.multiplyMM(matrix, 0, projection, 0, view, 0)
    }
    override fun onDrawFrame(gl: javax.microedition.khronos.opengles.GL10?) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        val next = target ?: return
        if (!initialized) { next.copyInto(smooth); initialized = true }
        else for (i in smooth.indices) smooth[i] += (next[i] - smooth[i]) * 0.35f
        val verts = FloatArray(bones.size * 3)
        for (i in bones.indices) {
            val idx = bones[i] * 3
            verts[i * 3] = smooth[idx] * 2.1f
            verts[i * 3 + 1] = smooth[idx + 1] * 2.1f
            verts[i * 3 + 2] = smooth[idx + 2] * 2.1f
        }
        val fb = ByteBuffer.allocateDirect(verts.size * 4).order(ByteOrder.nativeOrder()).asFloatBuffer().put(verts)
        fb.position(0)
        GLES20.glUseProgram(program)
        GLES20.glUniformMatrix4fv(GLES20.glGetUniformLocation(program, "m"), 1, false, matrix, 0)
        GLES20.glEnableVertexAttribArray(position)
        GLES20.glVertexAttribPointer(position, 3, GLES20.GL_FLOAT, false, 0, fb)
        GLES20.glLineWidth(7f)
        GLES20.glDrawArrays(GLES20.GL_LINES, 0, bones.size)
        GLES20.glDrawArrays(GLES20.GL_POINTS, 0, bones.size)
        GLES20.glDisableVertexAttribArray(position)
    }
}
