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
float3 m[4] = { float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) };
float3 s[4] = { float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) };
const float2 ox[4] = { float2(-1,-1), float2(1,-1), float2(-1,1), float2(1,1) };
float n = (R + 1) * (R + 1);
for (int k = 0; k < 4; k++)
{
    for (int i = 0; i <= R; i++)
    {
        for (int j = 0; j <= R; j++)
        {
            float3 t = SceneTextureLookup(ScreenUV + float2(i, j) * 0.4 * ox[k] * View.BufferSizeAndInvSize.zw, TexIndex, false).rgb;
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
    if (vs < best) { best = vs; c.rgb = mu; }
}
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
return c;