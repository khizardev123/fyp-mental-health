import type { NormalizedLandmark } from '@/lib/faceMeshAnalysis';

/** Key face contour loops for lightweight landmark visualization. */
const FACE_CONTOURS: number[][] = [
    [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10],
    [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 33],
    [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466, 263],
    [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185, 61],
];

export function drawFaceLandmarks(
    ctx: CanvasRenderingContext2D,
    landmarks: NormalizedLandmark[] | null | undefined,
    width: number,
    height: number,
    mirror = true,
) {
    ctx.clearRect(0, 0, width, height);
    if (!landmarks?.length) return;

    const toX = (x: number) => (mirror ? 1 - x : x) * width;
    const toY = (y: number) => y * height;

    ctx.strokeStyle = 'rgba(34, 211, 238, 0.55)';
    ctx.lineWidth = 1;
    for (const contour of FACE_CONTOURS) {
        ctx.beginPath();
        contour.forEach((idx, i) => {
            const lm = landmarks[idx];
            if (!lm) return;
            const x = toX(lm.x);
            const y = toY(lm.y);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
    }

    ctx.fillStyle = 'rgba(52, 211, 153, 0.9)';
    for (const lm of landmarks) {
        ctx.beginPath();
        ctx.arc(toX(lm.x), toY(lm.y), 1.1, 0, Math.PI * 2);
        ctx.fill();
    }
}
