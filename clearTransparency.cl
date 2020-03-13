const sampler_t sampler = CLK_NORMALIZED_COORDS_FALSE | CLK_FILTER_NEAREST | CLK_ADDRESS_CLAMP_TO_EDGE;

__kernel void clearTransparency(__read_only image2d_t in, __write_only image2d_t out) {
    int2 coords = (int2)(get_global_id(0), get_global_id(1));

    uint4 pxVal = read_imageui(in, sampler, coords);
    
    if (pxVal.w == 0) {
        write_imageui(out, coords, (uint4)(0));
    } else {
        write_imageui(out, coords, pxVal);
    }
}