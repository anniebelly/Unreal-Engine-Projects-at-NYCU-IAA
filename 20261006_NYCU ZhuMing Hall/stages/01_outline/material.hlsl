const float2 ScreenMult = View.ViewSizeAndInvSize.xy * View.BufferSizeAndInvSize.zw;
ScreenUV *= ScreenMult;
const int TexIndex = 14;
const float Thickness = 1.5;
const float Threshold = 0.03;
const float ColorThreshold = 0.25;
const float3 LineColor = float3(0.02, 0.02, 0.02);
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
c.rgb = lerp(c.rgb, LineColor, edge);
return c;