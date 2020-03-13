const sampler_t sampler = CLK_NORMALIZED_COORDS_FALSE | CLK_FILTER_NEAREST | CLK_ADDRESS_CLAMP_TO_EDGE;

__kernel void paste(__global __read_only int *in, __global __write_only int *out, int2 offset, int w, int oW) {
    int id = get_global_id(0);
    uint px = in[id];
    int x = id % w;
    int y = id / w;


}