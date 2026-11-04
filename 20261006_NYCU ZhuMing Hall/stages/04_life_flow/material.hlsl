const float2 ScreenMult = View.ViewSizeAndInvSize.xy * View.BufferSizeAndInvSize.zw;
ScreenUV *= ScreenMult;
const int TexIndex = 14;
const float Thickness = 1.5;
const float Threshold = 0.03;
const float ColorThreshold = 0.25;
float3 LineColor = float3(0.02, 0.02, 0.02);
float2 px = View.BufferSizeAndInvSize.zw * Thickness;
float4 c = SceneTextureLookup(ScreenUV, TexIndex, false);
// depth edges
float d = SceneTextureLookup(ScreenUV, 1, false).r;
float dL = SceneTextureLookup(ScreenUV - float2(px.x, 0.0), 1, false).r;
float dR = SceneTextureLookup(ScreenUV + float2(px.x, 0.0), 1, false).r;
float dU = SceneTextureLookup(ScreenUV - float2(0.0, px.y), 1, false).r;
float dD = SceneTextureLookup(ScreenUV + float2(0.0, px.y), 1, false).r;
float diff = (abs(dL - d) + abs(dR - d) + abs(dU - d) + abs(dD - d)) / max(d, 1.0);
float edge = smoothstep(Threshold, 2.0 * Threshold, diff);
// brightness edges, for the splat scan where depth has no lines
const float3 W = float3(0.3, 0.59, 0.11);
float l = dot(c.rgb, W);
float lL = dot(SceneTextureLookup(ScreenUV - float2(px.x, 0.0), TexIndex, false).rgb, W);
float lR = dot(SceneTextureLookup(ScreenUV + float2(px.x, 0.0), TexIndex, false).rgb, W);
float lU = dot(SceneTextureLookup(ScreenUV - float2(0.0, px.y), TexIndex, false).rgb, W);
float lD = dot(SceneTextureLookup(ScreenUV + float2(0.0, px.y), TexIndex, false).rgb, W);
float ldiff = abs(lL - l) + abs(lR - l) + abs(lU - l) + abs(lD - l);
edge = max(edge, smoothstep(ColorThreshold, 2.0 * ColorThreshold, ldiff));
const int R = 3;
// Life-vein flow: soil = near the ground plane (PlayerStart -> preview mesh) and not green; everything above
// (trunks, leaves) streams upward. Grey/white/black (non-living: buildings, iron gates) stays still. The upward stream uses two crossfaded phases so it loops without a jump.
float soil = 0.0;
float green = 0.0;
float tt = View.GameTime;
float2 circ = float2(0.0, 0.0);
float upPhase = 0.0;
float alive = 0.0;
if (1)
{
    const float3 GA = float3(256.31994059888535, -72.11163603319427, -10.0);
    const float3 GB = float3(638.9953536580487, 248.9961012561818, -137.45454545454544);
    float2 gab = GB.xy - GA.xy;
    float gt = dot(WorldPos.xy - GA.xy, gab) / max(dot(gab, gab), 1.0);
    float above = WorldPos.z - lerp(GA.z, GB.z, gt);
    green = saturate((c.g - max(c.r, c.b)) * 4.0);
    float cmax = max(c.r, max(c.g, c.b));
    float sat = (cmax - min(c.r, min(c.g, c.b))) / max(cmax, 0.001);
    float brown = smoothstep(0.02, 0.1, c.r - c.b);
    alive = smoothstep(0.12, 0.25, sat) * max(green, brown);
    soil = (1.0 - smoothstep(50.0, 50.0 * 1.6, above)) * (1.0 - green);
    float ph = dot(WorldPos.xy, float2(0.013, 0.017));
    circ = float2(cos(tt * 1.2 + ph), sin(tt * 1.2 + ph)) * 3.0;
    upPhase = tt * 0.35 * lerp(1.0, 4.68, green) + sin(dot(WorldPos.xy, float2(0.004, 0.003))) * 0.25;
}
float3 res[2] = { c.rgb, c.rgb };
float wsum[2] = { 0.5, 0.5 };
const float2 ox[4] = { float2(-1,-1), float2(1,-1), float2(-1,1), float2(1,1) };
float n = (R + 1) * (R + 1);
for (int layer = 0; layer < (1 ? 2 : 1); layer++)
{
    float p = frac(upPhase + layer * 0.5);
    wsum[layer] = 1 ? 1.0 - abs(2.0 * p - 1.0) : 1.0;
    float2 off = lerp(float2(0.0, p * 7.2), circ, soil) * alive * View.BufferSizeAndInvSize.zw;
    float3 m[4] = { float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) };
    float3 s[4] = { float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) };
    for (int k = 0; k < 4; k++)
    {
        for (int i = 0; i <= R; i++)
        {
            for (int j = 0; j <= R; j++)
            {
                float3 t = SceneTextureLookup(ScreenUV + off + float2(i, j) * 0.4 * ox[k] * View.BufferSizeAndInvSize.zw, TexIndex, false).rgb;
                m[k] += t;
                s[k] += t * t;
            }
        }
    }
    float best = 1e9;
    for (int q = 0; q < 4; q++)
    {
        float3 mu = m[q] / n;
        float3 v = abs(s[q] / n - mu * mu);
        float vs = v.r + v.g + v.b;
        if (vs < best) { best = vs; res[layer] = mu; }
    }
}
c.rgb = 1 ? (res[0] * wsum[0] + res[1] * wsum[1]) / max(wsum[0] + wsum[1], 0.001) : res[0];
c.rgb = saturate((c.rgb - 0.3) * 1.36 + 0.3);
float lum = dot(c.rgb, W);
if (6 > 0)
{
    float b = lum * 6;
    float q = (floor(b) + smoothstep(0.3, 0.7, frac(b))) / 6;
    c.rgb *= q / max(lum, 0.001);
    lum = q;
}
c.rgb = lerp(float3(lum, lum, lum), c.rgb, 1.4);
c.rgb = lerp(c.rgb, c.rgb * float3(1.0, 0.93, 0.76) * 1.08, saturate(lum * 1.5));
c.rgb = lerp(c.rgb, float3(1, 1, 1), 0.1 * saturate(lum * 1.5));
c.rgb *= 1.0 + 0.4 * smoothstep(0.4, 0.85, lum);
c.rgb *= 1.1;
c.rgb = max(c.rgb, 0.0);
float road = 0.0;
if (1)
{
    const float3 A = float3(256.31994059888535, -72.11163603319427, -10.0);
    const float3 B = float3(638.9953536580487, 248.9961012561818, -137.45454545454544);
    float2 ab = B.xy - A.xy;
    float t = saturate(dot(WorldPos.xy - A.xy, ab) / max(dot(ab, ab), 1.0));
    float dist = length(WorldPos.xy - (A.xy + ab * t));
    float above = WorldPos.z - lerp(A.z, B.z, t);
    road = (1.0 - smoothstep(170.0, 170.0 + 140.0, dist)) * (1.0 - smoothstep(120.0 * 0.5, 120.0, above));
    road *= 1.0 - 0.35 * saturate(dist / 170.0);  // hotter down the middle, like a spotlight
    c.rgb = lerp(c.rgb, c.rgb * (1.0 + 1.1) * float3(1.0, 0.94, 0.8) + float3(1.0, 0.94, 0.8) * 0.06 * 1.1, road);
}
LineColor = float3(0.05, 0.05, 0.11);
c.rgb = lerp(c.rgb, LineColor, smoothstep(0.224, 0.08, lum) * (1.0 - road));
edge *= 1.0;
c.rgb = lerp(c.rgb, LineColor, edge);
if (1)
{
    const float3 SunDir = float3(-0.19973703101655327, 0.06950939668032119, 0.977380970867466);
    float4 sc = mul(float4(View.TranslatedWorldCameraOrigin + SunDir * 1000000.0, 1.0), View.TranslatedWorldToClip);
    if (sc.w > 0.0)
    {
        float2 sunUV = ((sc.xy / sc.w) * float2(0.5, -0.5) + 0.5) * ScreenMult;
        float2 delta = (sunUV - ScreenUV) * 0.9 / 48;
        float2 ruv = ScreenUV;
        float illum = 1.0;
        float acc = 0.0;
        for (int r = 0; r < 48; r++)
        {
            ruv += delta;
            float rl = dot(SceneTextureLookup(ruv, TexIndex, false).rgb, W);
            float rd = SceneTextureLookup(ruv, 1, false).r;
            acc += smoothstep(0.45, 0.85, rl) * smoothstep(3000.0, 3000.0 * 2.5, rd) * illum;
            illum *= 0.965;
        }
        acc /= 48;
        float fade = 1.0 - smoothstep(0.6, 1.4, length(sunUV / ScreenMult - 0.5));
        c.rgb += float3(1.0, 0.9, 0.68) * acc * 2.2 * fade;
    }
}
return c;