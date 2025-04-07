#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.13.2                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_5382296959486538598) {
   out_5382296959486538598[0] = delta_x[0] + nom_x[0];
   out_5382296959486538598[1] = delta_x[1] + nom_x[1];
   out_5382296959486538598[2] = delta_x[2] + nom_x[2];
   out_5382296959486538598[3] = delta_x[3] + nom_x[3];
   out_5382296959486538598[4] = delta_x[4] + nom_x[4];
   out_5382296959486538598[5] = delta_x[5] + nom_x[5];
   out_5382296959486538598[6] = delta_x[6] + nom_x[6];
   out_5382296959486538598[7] = delta_x[7] + nom_x[7];
   out_5382296959486538598[8] = delta_x[8] + nom_x[8];
   out_5382296959486538598[9] = delta_x[9] + nom_x[9];
   out_5382296959486538598[10] = delta_x[10] + nom_x[10];
   out_5382296959486538598[11] = delta_x[11] + nom_x[11];
   out_5382296959486538598[12] = delta_x[12] + nom_x[12];
   out_5382296959486538598[13] = delta_x[13] + nom_x[13];
   out_5382296959486538598[14] = delta_x[14] + nom_x[14];
   out_5382296959486538598[15] = delta_x[15] + nom_x[15];
   out_5382296959486538598[16] = delta_x[16] + nom_x[16];
   out_5382296959486538598[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1423671362174335144) {
   out_1423671362174335144[0] = -nom_x[0] + true_x[0];
   out_1423671362174335144[1] = -nom_x[1] + true_x[1];
   out_1423671362174335144[2] = -nom_x[2] + true_x[2];
   out_1423671362174335144[3] = -nom_x[3] + true_x[3];
   out_1423671362174335144[4] = -nom_x[4] + true_x[4];
   out_1423671362174335144[5] = -nom_x[5] + true_x[5];
   out_1423671362174335144[6] = -nom_x[6] + true_x[6];
   out_1423671362174335144[7] = -nom_x[7] + true_x[7];
   out_1423671362174335144[8] = -nom_x[8] + true_x[8];
   out_1423671362174335144[9] = -nom_x[9] + true_x[9];
   out_1423671362174335144[10] = -nom_x[10] + true_x[10];
   out_1423671362174335144[11] = -nom_x[11] + true_x[11];
   out_1423671362174335144[12] = -nom_x[12] + true_x[12];
   out_1423671362174335144[13] = -nom_x[13] + true_x[13];
   out_1423671362174335144[14] = -nom_x[14] + true_x[14];
   out_1423671362174335144[15] = -nom_x[15] + true_x[15];
   out_1423671362174335144[16] = -nom_x[16] + true_x[16];
   out_1423671362174335144[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_6640898992211347549) {
   out_6640898992211347549[0] = 1.0;
   out_6640898992211347549[1] = 0.0;
   out_6640898992211347549[2] = 0.0;
   out_6640898992211347549[3] = 0.0;
   out_6640898992211347549[4] = 0.0;
   out_6640898992211347549[5] = 0.0;
   out_6640898992211347549[6] = 0.0;
   out_6640898992211347549[7] = 0.0;
   out_6640898992211347549[8] = 0.0;
   out_6640898992211347549[9] = 0.0;
   out_6640898992211347549[10] = 0.0;
   out_6640898992211347549[11] = 0.0;
   out_6640898992211347549[12] = 0.0;
   out_6640898992211347549[13] = 0.0;
   out_6640898992211347549[14] = 0.0;
   out_6640898992211347549[15] = 0.0;
   out_6640898992211347549[16] = 0.0;
   out_6640898992211347549[17] = 0.0;
   out_6640898992211347549[18] = 0.0;
   out_6640898992211347549[19] = 1.0;
   out_6640898992211347549[20] = 0.0;
   out_6640898992211347549[21] = 0.0;
   out_6640898992211347549[22] = 0.0;
   out_6640898992211347549[23] = 0.0;
   out_6640898992211347549[24] = 0.0;
   out_6640898992211347549[25] = 0.0;
   out_6640898992211347549[26] = 0.0;
   out_6640898992211347549[27] = 0.0;
   out_6640898992211347549[28] = 0.0;
   out_6640898992211347549[29] = 0.0;
   out_6640898992211347549[30] = 0.0;
   out_6640898992211347549[31] = 0.0;
   out_6640898992211347549[32] = 0.0;
   out_6640898992211347549[33] = 0.0;
   out_6640898992211347549[34] = 0.0;
   out_6640898992211347549[35] = 0.0;
   out_6640898992211347549[36] = 0.0;
   out_6640898992211347549[37] = 0.0;
   out_6640898992211347549[38] = 1.0;
   out_6640898992211347549[39] = 0.0;
   out_6640898992211347549[40] = 0.0;
   out_6640898992211347549[41] = 0.0;
   out_6640898992211347549[42] = 0.0;
   out_6640898992211347549[43] = 0.0;
   out_6640898992211347549[44] = 0.0;
   out_6640898992211347549[45] = 0.0;
   out_6640898992211347549[46] = 0.0;
   out_6640898992211347549[47] = 0.0;
   out_6640898992211347549[48] = 0.0;
   out_6640898992211347549[49] = 0.0;
   out_6640898992211347549[50] = 0.0;
   out_6640898992211347549[51] = 0.0;
   out_6640898992211347549[52] = 0.0;
   out_6640898992211347549[53] = 0.0;
   out_6640898992211347549[54] = 0.0;
   out_6640898992211347549[55] = 0.0;
   out_6640898992211347549[56] = 0.0;
   out_6640898992211347549[57] = 1.0;
   out_6640898992211347549[58] = 0.0;
   out_6640898992211347549[59] = 0.0;
   out_6640898992211347549[60] = 0.0;
   out_6640898992211347549[61] = 0.0;
   out_6640898992211347549[62] = 0.0;
   out_6640898992211347549[63] = 0.0;
   out_6640898992211347549[64] = 0.0;
   out_6640898992211347549[65] = 0.0;
   out_6640898992211347549[66] = 0.0;
   out_6640898992211347549[67] = 0.0;
   out_6640898992211347549[68] = 0.0;
   out_6640898992211347549[69] = 0.0;
   out_6640898992211347549[70] = 0.0;
   out_6640898992211347549[71] = 0.0;
   out_6640898992211347549[72] = 0.0;
   out_6640898992211347549[73] = 0.0;
   out_6640898992211347549[74] = 0.0;
   out_6640898992211347549[75] = 0.0;
   out_6640898992211347549[76] = 1.0;
   out_6640898992211347549[77] = 0.0;
   out_6640898992211347549[78] = 0.0;
   out_6640898992211347549[79] = 0.0;
   out_6640898992211347549[80] = 0.0;
   out_6640898992211347549[81] = 0.0;
   out_6640898992211347549[82] = 0.0;
   out_6640898992211347549[83] = 0.0;
   out_6640898992211347549[84] = 0.0;
   out_6640898992211347549[85] = 0.0;
   out_6640898992211347549[86] = 0.0;
   out_6640898992211347549[87] = 0.0;
   out_6640898992211347549[88] = 0.0;
   out_6640898992211347549[89] = 0.0;
   out_6640898992211347549[90] = 0.0;
   out_6640898992211347549[91] = 0.0;
   out_6640898992211347549[92] = 0.0;
   out_6640898992211347549[93] = 0.0;
   out_6640898992211347549[94] = 0.0;
   out_6640898992211347549[95] = 1.0;
   out_6640898992211347549[96] = 0.0;
   out_6640898992211347549[97] = 0.0;
   out_6640898992211347549[98] = 0.0;
   out_6640898992211347549[99] = 0.0;
   out_6640898992211347549[100] = 0.0;
   out_6640898992211347549[101] = 0.0;
   out_6640898992211347549[102] = 0.0;
   out_6640898992211347549[103] = 0.0;
   out_6640898992211347549[104] = 0.0;
   out_6640898992211347549[105] = 0.0;
   out_6640898992211347549[106] = 0.0;
   out_6640898992211347549[107] = 0.0;
   out_6640898992211347549[108] = 0.0;
   out_6640898992211347549[109] = 0.0;
   out_6640898992211347549[110] = 0.0;
   out_6640898992211347549[111] = 0.0;
   out_6640898992211347549[112] = 0.0;
   out_6640898992211347549[113] = 0.0;
   out_6640898992211347549[114] = 1.0;
   out_6640898992211347549[115] = 0.0;
   out_6640898992211347549[116] = 0.0;
   out_6640898992211347549[117] = 0.0;
   out_6640898992211347549[118] = 0.0;
   out_6640898992211347549[119] = 0.0;
   out_6640898992211347549[120] = 0.0;
   out_6640898992211347549[121] = 0.0;
   out_6640898992211347549[122] = 0.0;
   out_6640898992211347549[123] = 0.0;
   out_6640898992211347549[124] = 0.0;
   out_6640898992211347549[125] = 0.0;
   out_6640898992211347549[126] = 0.0;
   out_6640898992211347549[127] = 0.0;
   out_6640898992211347549[128] = 0.0;
   out_6640898992211347549[129] = 0.0;
   out_6640898992211347549[130] = 0.0;
   out_6640898992211347549[131] = 0.0;
   out_6640898992211347549[132] = 0.0;
   out_6640898992211347549[133] = 1.0;
   out_6640898992211347549[134] = 0.0;
   out_6640898992211347549[135] = 0.0;
   out_6640898992211347549[136] = 0.0;
   out_6640898992211347549[137] = 0.0;
   out_6640898992211347549[138] = 0.0;
   out_6640898992211347549[139] = 0.0;
   out_6640898992211347549[140] = 0.0;
   out_6640898992211347549[141] = 0.0;
   out_6640898992211347549[142] = 0.0;
   out_6640898992211347549[143] = 0.0;
   out_6640898992211347549[144] = 0.0;
   out_6640898992211347549[145] = 0.0;
   out_6640898992211347549[146] = 0.0;
   out_6640898992211347549[147] = 0.0;
   out_6640898992211347549[148] = 0.0;
   out_6640898992211347549[149] = 0.0;
   out_6640898992211347549[150] = 0.0;
   out_6640898992211347549[151] = 0.0;
   out_6640898992211347549[152] = 1.0;
   out_6640898992211347549[153] = 0.0;
   out_6640898992211347549[154] = 0.0;
   out_6640898992211347549[155] = 0.0;
   out_6640898992211347549[156] = 0.0;
   out_6640898992211347549[157] = 0.0;
   out_6640898992211347549[158] = 0.0;
   out_6640898992211347549[159] = 0.0;
   out_6640898992211347549[160] = 0.0;
   out_6640898992211347549[161] = 0.0;
   out_6640898992211347549[162] = 0.0;
   out_6640898992211347549[163] = 0.0;
   out_6640898992211347549[164] = 0.0;
   out_6640898992211347549[165] = 0.0;
   out_6640898992211347549[166] = 0.0;
   out_6640898992211347549[167] = 0.0;
   out_6640898992211347549[168] = 0.0;
   out_6640898992211347549[169] = 0.0;
   out_6640898992211347549[170] = 0.0;
   out_6640898992211347549[171] = 1.0;
   out_6640898992211347549[172] = 0.0;
   out_6640898992211347549[173] = 0.0;
   out_6640898992211347549[174] = 0.0;
   out_6640898992211347549[175] = 0.0;
   out_6640898992211347549[176] = 0.0;
   out_6640898992211347549[177] = 0.0;
   out_6640898992211347549[178] = 0.0;
   out_6640898992211347549[179] = 0.0;
   out_6640898992211347549[180] = 0.0;
   out_6640898992211347549[181] = 0.0;
   out_6640898992211347549[182] = 0.0;
   out_6640898992211347549[183] = 0.0;
   out_6640898992211347549[184] = 0.0;
   out_6640898992211347549[185] = 0.0;
   out_6640898992211347549[186] = 0.0;
   out_6640898992211347549[187] = 0.0;
   out_6640898992211347549[188] = 0.0;
   out_6640898992211347549[189] = 0.0;
   out_6640898992211347549[190] = 1.0;
   out_6640898992211347549[191] = 0.0;
   out_6640898992211347549[192] = 0.0;
   out_6640898992211347549[193] = 0.0;
   out_6640898992211347549[194] = 0.0;
   out_6640898992211347549[195] = 0.0;
   out_6640898992211347549[196] = 0.0;
   out_6640898992211347549[197] = 0.0;
   out_6640898992211347549[198] = 0.0;
   out_6640898992211347549[199] = 0.0;
   out_6640898992211347549[200] = 0.0;
   out_6640898992211347549[201] = 0.0;
   out_6640898992211347549[202] = 0.0;
   out_6640898992211347549[203] = 0.0;
   out_6640898992211347549[204] = 0.0;
   out_6640898992211347549[205] = 0.0;
   out_6640898992211347549[206] = 0.0;
   out_6640898992211347549[207] = 0.0;
   out_6640898992211347549[208] = 0.0;
   out_6640898992211347549[209] = 1.0;
   out_6640898992211347549[210] = 0.0;
   out_6640898992211347549[211] = 0.0;
   out_6640898992211347549[212] = 0.0;
   out_6640898992211347549[213] = 0.0;
   out_6640898992211347549[214] = 0.0;
   out_6640898992211347549[215] = 0.0;
   out_6640898992211347549[216] = 0.0;
   out_6640898992211347549[217] = 0.0;
   out_6640898992211347549[218] = 0.0;
   out_6640898992211347549[219] = 0.0;
   out_6640898992211347549[220] = 0.0;
   out_6640898992211347549[221] = 0.0;
   out_6640898992211347549[222] = 0.0;
   out_6640898992211347549[223] = 0.0;
   out_6640898992211347549[224] = 0.0;
   out_6640898992211347549[225] = 0.0;
   out_6640898992211347549[226] = 0.0;
   out_6640898992211347549[227] = 0.0;
   out_6640898992211347549[228] = 1.0;
   out_6640898992211347549[229] = 0.0;
   out_6640898992211347549[230] = 0.0;
   out_6640898992211347549[231] = 0.0;
   out_6640898992211347549[232] = 0.0;
   out_6640898992211347549[233] = 0.0;
   out_6640898992211347549[234] = 0.0;
   out_6640898992211347549[235] = 0.0;
   out_6640898992211347549[236] = 0.0;
   out_6640898992211347549[237] = 0.0;
   out_6640898992211347549[238] = 0.0;
   out_6640898992211347549[239] = 0.0;
   out_6640898992211347549[240] = 0.0;
   out_6640898992211347549[241] = 0.0;
   out_6640898992211347549[242] = 0.0;
   out_6640898992211347549[243] = 0.0;
   out_6640898992211347549[244] = 0.0;
   out_6640898992211347549[245] = 0.0;
   out_6640898992211347549[246] = 0.0;
   out_6640898992211347549[247] = 1.0;
   out_6640898992211347549[248] = 0.0;
   out_6640898992211347549[249] = 0.0;
   out_6640898992211347549[250] = 0.0;
   out_6640898992211347549[251] = 0.0;
   out_6640898992211347549[252] = 0.0;
   out_6640898992211347549[253] = 0.0;
   out_6640898992211347549[254] = 0.0;
   out_6640898992211347549[255] = 0.0;
   out_6640898992211347549[256] = 0.0;
   out_6640898992211347549[257] = 0.0;
   out_6640898992211347549[258] = 0.0;
   out_6640898992211347549[259] = 0.0;
   out_6640898992211347549[260] = 0.0;
   out_6640898992211347549[261] = 0.0;
   out_6640898992211347549[262] = 0.0;
   out_6640898992211347549[263] = 0.0;
   out_6640898992211347549[264] = 0.0;
   out_6640898992211347549[265] = 0.0;
   out_6640898992211347549[266] = 1.0;
   out_6640898992211347549[267] = 0.0;
   out_6640898992211347549[268] = 0.0;
   out_6640898992211347549[269] = 0.0;
   out_6640898992211347549[270] = 0.0;
   out_6640898992211347549[271] = 0.0;
   out_6640898992211347549[272] = 0.0;
   out_6640898992211347549[273] = 0.0;
   out_6640898992211347549[274] = 0.0;
   out_6640898992211347549[275] = 0.0;
   out_6640898992211347549[276] = 0.0;
   out_6640898992211347549[277] = 0.0;
   out_6640898992211347549[278] = 0.0;
   out_6640898992211347549[279] = 0.0;
   out_6640898992211347549[280] = 0.0;
   out_6640898992211347549[281] = 0.0;
   out_6640898992211347549[282] = 0.0;
   out_6640898992211347549[283] = 0.0;
   out_6640898992211347549[284] = 0.0;
   out_6640898992211347549[285] = 1.0;
   out_6640898992211347549[286] = 0.0;
   out_6640898992211347549[287] = 0.0;
   out_6640898992211347549[288] = 0.0;
   out_6640898992211347549[289] = 0.0;
   out_6640898992211347549[290] = 0.0;
   out_6640898992211347549[291] = 0.0;
   out_6640898992211347549[292] = 0.0;
   out_6640898992211347549[293] = 0.0;
   out_6640898992211347549[294] = 0.0;
   out_6640898992211347549[295] = 0.0;
   out_6640898992211347549[296] = 0.0;
   out_6640898992211347549[297] = 0.0;
   out_6640898992211347549[298] = 0.0;
   out_6640898992211347549[299] = 0.0;
   out_6640898992211347549[300] = 0.0;
   out_6640898992211347549[301] = 0.0;
   out_6640898992211347549[302] = 0.0;
   out_6640898992211347549[303] = 0.0;
   out_6640898992211347549[304] = 1.0;
   out_6640898992211347549[305] = 0.0;
   out_6640898992211347549[306] = 0.0;
   out_6640898992211347549[307] = 0.0;
   out_6640898992211347549[308] = 0.0;
   out_6640898992211347549[309] = 0.0;
   out_6640898992211347549[310] = 0.0;
   out_6640898992211347549[311] = 0.0;
   out_6640898992211347549[312] = 0.0;
   out_6640898992211347549[313] = 0.0;
   out_6640898992211347549[314] = 0.0;
   out_6640898992211347549[315] = 0.0;
   out_6640898992211347549[316] = 0.0;
   out_6640898992211347549[317] = 0.0;
   out_6640898992211347549[318] = 0.0;
   out_6640898992211347549[319] = 0.0;
   out_6640898992211347549[320] = 0.0;
   out_6640898992211347549[321] = 0.0;
   out_6640898992211347549[322] = 0.0;
   out_6640898992211347549[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_5710795834153600449) {
   out_5710795834153600449[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_5710795834153600449[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_5710795834153600449[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_5710795834153600449[3] = dt*state[12] + state[3];
   out_5710795834153600449[4] = dt*state[13] + state[4];
   out_5710795834153600449[5] = dt*state[14] + state[5];
   out_5710795834153600449[6] = state[6];
   out_5710795834153600449[7] = state[7];
   out_5710795834153600449[8] = state[8];
   out_5710795834153600449[9] = state[9];
   out_5710795834153600449[10] = state[10];
   out_5710795834153600449[11] = state[11];
   out_5710795834153600449[12] = state[12];
   out_5710795834153600449[13] = state[13];
   out_5710795834153600449[14] = state[14];
   out_5710795834153600449[15] = state[15];
   out_5710795834153600449[16] = state[16];
   out_5710795834153600449[17] = state[17];
}
void F_fun(double *state, double dt, double *out_5041739674699220760) {
   out_5041739674699220760[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5041739674699220760[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5041739674699220760[2] = 0;
   out_5041739674699220760[3] = 0;
   out_5041739674699220760[4] = 0;
   out_5041739674699220760[5] = 0;
   out_5041739674699220760[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5041739674699220760[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5041739674699220760[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5041739674699220760[9] = 0;
   out_5041739674699220760[10] = 0;
   out_5041739674699220760[11] = 0;
   out_5041739674699220760[12] = 0;
   out_5041739674699220760[13] = 0;
   out_5041739674699220760[14] = 0;
   out_5041739674699220760[15] = 0;
   out_5041739674699220760[16] = 0;
   out_5041739674699220760[17] = 0;
   out_5041739674699220760[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5041739674699220760[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5041739674699220760[20] = 0;
   out_5041739674699220760[21] = 0;
   out_5041739674699220760[22] = 0;
   out_5041739674699220760[23] = 0;
   out_5041739674699220760[24] = 0;
   out_5041739674699220760[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5041739674699220760[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5041739674699220760[27] = 0;
   out_5041739674699220760[28] = 0;
   out_5041739674699220760[29] = 0;
   out_5041739674699220760[30] = 0;
   out_5041739674699220760[31] = 0;
   out_5041739674699220760[32] = 0;
   out_5041739674699220760[33] = 0;
   out_5041739674699220760[34] = 0;
   out_5041739674699220760[35] = 0;
   out_5041739674699220760[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5041739674699220760[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5041739674699220760[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5041739674699220760[39] = 0;
   out_5041739674699220760[40] = 0;
   out_5041739674699220760[41] = 0;
   out_5041739674699220760[42] = 0;
   out_5041739674699220760[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5041739674699220760[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5041739674699220760[45] = 0;
   out_5041739674699220760[46] = 0;
   out_5041739674699220760[47] = 0;
   out_5041739674699220760[48] = 0;
   out_5041739674699220760[49] = 0;
   out_5041739674699220760[50] = 0;
   out_5041739674699220760[51] = 0;
   out_5041739674699220760[52] = 0;
   out_5041739674699220760[53] = 0;
   out_5041739674699220760[54] = 0;
   out_5041739674699220760[55] = 0;
   out_5041739674699220760[56] = 0;
   out_5041739674699220760[57] = 1;
   out_5041739674699220760[58] = 0;
   out_5041739674699220760[59] = 0;
   out_5041739674699220760[60] = 0;
   out_5041739674699220760[61] = 0;
   out_5041739674699220760[62] = 0;
   out_5041739674699220760[63] = 0;
   out_5041739674699220760[64] = 0;
   out_5041739674699220760[65] = 0;
   out_5041739674699220760[66] = dt;
   out_5041739674699220760[67] = 0;
   out_5041739674699220760[68] = 0;
   out_5041739674699220760[69] = 0;
   out_5041739674699220760[70] = 0;
   out_5041739674699220760[71] = 0;
   out_5041739674699220760[72] = 0;
   out_5041739674699220760[73] = 0;
   out_5041739674699220760[74] = 0;
   out_5041739674699220760[75] = 0;
   out_5041739674699220760[76] = 1;
   out_5041739674699220760[77] = 0;
   out_5041739674699220760[78] = 0;
   out_5041739674699220760[79] = 0;
   out_5041739674699220760[80] = 0;
   out_5041739674699220760[81] = 0;
   out_5041739674699220760[82] = 0;
   out_5041739674699220760[83] = 0;
   out_5041739674699220760[84] = 0;
   out_5041739674699220760[85] = dt;
   out_5041739674699220760[86] = 0;
   out_5041739674699220760[87] = 0;
   out_5041739674699220760[88] = 0;
   out_5041739674699220760[89] = 0;
   out_5041739674699220760[90] = 0;
   out_5041739674699220760[91] = 0;
   out_5041739674699220760[92] = 0;
   out_5041739674699220760[93] = 0;
   out_5041739674699220760[94] = 0;
   out_5041739674699220760[95] = 1;
   out_5041739674699220760[96] = 0;
   out_5041739674699220760[97] = 0;
   out_5041739674699220760[98] = 0;
   out_5041739674699220760[99] = 0;
   out_5041739674699220760[100] = 0;
   out_5041739674699220760[101] = 0;
   out_5041739674699220760[102] = 0;
   out_5041739674699220760[103] = 0;
   out_5041739674699220760[104] = dt;
   out_5041739674699220760[105] = 0;
   out_5041739674699220760[106] = 0;
   out_5041739674699220760[107] = 0;
   out_5041739674699220760[108] = 0;
   out_5041739674699220760[109] = 0;
   out_5041739674699220760[110] = 0;
   out_5041739674699220760[111] = 0;
   out_5041739674699220760[112] = 0;
   out_5041739674699220760[113] = 0;
   out_5041739674699220760[114] = 1;
   out_5041739674699220760[115] = 0;
   out_5041739674699220760[116] = 0;
   out_5041739674699220760[117] = 0;
   out_5041739674699220760[118] = 0;
   out_5041739674699220760[119] = 0;
   out_5041739674699220760[120] = 0;
   out_5041739674699220760[121] = 0;
   out_5041739674699220760[122] = 0;
   out_5041739674699220760[123] = 0;
   out_5041739674699220760[124] = 0;
   out_5041739674699220760[125] = 0;
   out_5041739674699220760[126] = 0;
   out_5041739674699220760[127] = 0;
   out_5041739674699220760[128] = 0;
   out_5041739674699220760[129] = 0;
   out_5041739674699220760[130] = 0;
   out_5041739674699220760[131] = 0;
   out_5041739674699220760[132] = 0;
   out_5041739674699220760[133] = 1;
   out_5041739674699220760[134] = 0;
   out_5041739674699220760[135] = 0;
   out_5041739674699220760[136] = 0;
   out_5041739674699220760[137] = 0;
   out_5041739674699220760[138] = 0;
   out_5041739674699220760[139] = 0;
   out_5041739674699220760[140] = 0;
   out_5041739674699220760[141] = 0;
   out_5041739674699220760[142] = 0;
   out_5041739674699220760[143] = 0;
   out_5041739674699220760[144] = 0;
   out_5041739674699220760[145] = 0;
   out_5041739674699220760[146] = 0;
   out_5041739674699220760[147] = 0;
   out_5041739674699220760[148] = 0;
   out_5041739674699220760[149] = 0;
   out_5041739674699220760[150] = 0;
   out_5041739674699220760[151] = 0;
   out_5041739674699220760[152] = 1;
   out_5041739674699220760[153] = 0;
   out_5041739674699220760[154] = 0;
   out_5041739674699220760[155] = 0;
   out_5041739674699220760[156] = 0;
   out_5041739674699220760[157] = 0;
   out_5041739674699220760[158] = 0;
   out_5041739674699220760[159] = 0;
   out_5041739674699220760[160] = 0;
   out_5041739674699220760[161] = 0;
   out_5041739674699220760[162] = 0;
   out_5041739674699220760[163] = 0;
   out_5041739674699220760[164] = 0;
   out_5041739674699220760[165] = 0;
   out_5041739674699220760[166] = 0;
   out_5041739674699220760[167] = 0;
   out_5041739674699220760[168] = 0;
   out_5041739674699220760[169] = 0;
   out_5041739674699220760[170] = 0;
   out_5041739674699220760[171] = 1;
   out_5041739674699220760[172] = 0;
   out_5041739674699220760[173] = 0;
   out_5041739674699220760[174] = 0;
   out_5041739674699220760[175] = 0;
   out_5041739674699220760[176] = 0;
   out_5041739674699220760[177] = 0;
   out_5041739674699220760[178] = 0;
   out_5041739674699220760[179] = 0;
   out_5041739674699220760[180] = 0;
   out_5041739674699220760[181] = 0;
   out_5041739674699220760[182] = 0;
   out_5041739674699220760[183] = 0;
   out_5041739674699220760[184] = 0;
   out_5041739674699220760[185] = 0;
   out_5041739674699220760[186] = 0;
   out_5041739674699220760[187] = 0;
   out_5041739674699220760[188] = 0;
   out_5041739674699220760[189] = 0;
   out_5041739674699220760[190] = 1;
   out_5041739674699220760[191] = 0;
   out_5041739674699220760[192] = 0;
   out_5041739674699220760[193] = 0;
   out_5041739674699220760[194] = 0;
   out_5041739674699220760[195] = 0;
   out_5041739674699220760[196] = 0;
   out_5041739674699220760[197] = 0;
   out_5041739674699220760[198] = 0;
   out_5041739674699220760[199] = 0;
   out_5041739674699220760[200] = 0;
   out_5041739674699220760[201] = 0;
   out_5041739674699220760[202] = 0;
   out_5041739674699220760[203] = 0;
   out_5041739674699220760[204] = 0;
   out_5041739674699220760[205] = 0;
   out_5041739674699220760[206] = 0;
   out_5041739674699220760[207] = 0;
   out_5041739674699220760[208] = 0;
   out_5041739674699220760[209] = 1;
   out_5041739674699220760[210] = 0;
   out_5041739674699220760[211] = 0;
   out_5041739674699220760[212] = 0;
   out_5041739674699220760[213] = 0;
   out_5041739674699220760[214] = 0;
   out_5041739674699220760[215] = 0;
   out_5041739674699220760[216] = 0;
   out_5041739674699220760[217] = 0;
   out_5041739674699220760[218] = 0;
   out_5041739674699220760[219] = 0;
   out_5041739674699220760[220] = 0;
   out_5041739674699220760[221] = 0;
   out_5041739674699220760[222] = 0;
   out_5041739674699220760[223] = 0;
   out_5041739674699220760[224] = 0;
   out_5041739674699220760[225] = 0;
   out_5041739674699220760[226] = 0;
   out_5041739674699220760[227] = 0;
   out_5041739674699220760[228] = 1;
   out_5041739674699220760[229] = 0;
   out_5041739674699220760[230] = 0;
   out_5041739674699220760[231] = 0;
   out_5041739674699220760[232] = 0;
   out_5041739674699220760[233] = 0;
   out_5041739674699220760[234] = 0;
   out_5041739674699220760[235] = 0;
   out_5041739674699220760[236] = 0;
   out_5041739674699220760[237] = 0;
   out_5041739674699220760[238] = 0;
   out_5041739674699220760[239] = 0;
   out_5041739674699220760[240] = 0;
   out_5041739674699220760[241] = 0;
   out_5041739674699220760[242] = 0;
   out_5041739674699220760[243] = 0;
   out_5041739674699220760[244] = 0;
   out_5041739674699220760[245] = 0;
   out_5041739674699220760[246] = 0;
   out_5041739674699220760[247] = 1;
   out_5041739674699220760[248] = 0;
   out_5041739674699220760[249] = 0;
   out_5041739674699220760[250] = 0;
   out_5041739674699220760[251] = 0;
   out_5041739674699220760[252] = 0;
   out_5041739674699220760[253] = 0;
   out_5041739674699220760[254] = 0;
   out_5041739674699220760[255] = 0;
   out_5041739674699220760[256] = 0;
   out_5041739674699220760[257] = 0;
   out_5041739674699220760[258] = 0;
   out_5041739674699220760[259] = 0;
   out_5041739674699220760[260] = 0;
   out_5041739674699220760[261] = 0;
   out_5041739674699220760[262] = 0;
   out_5041739674699220760[263] = 0;
   out_5041739674699220760[264] = 0;
   out_5041739674699220760[265] = 0;
   out_5041739674699220760[266] = 1;
   out_5041739674699220760[267] = 0;
   out_5041739674699220760[268] = 0;
   out_5041739674699220760[269] = 0;
   out_5041739674699220760[270] = 0;
   out_5041739674699220760[271] = 0;
   out_5041739674699220760[272] = 0;
   out_5041739674699220760[273] = 0;
   out_5041739674699220760[274] = 0;
   out_5041739674699220760[275] = 0;
   out_5041739674699220760[276] = 0;
   out_5041739674699220760[277] = 0;
   out_5041739674699220760[278] = 0;
   out_5041739674699220760[279] = 0;
   out_5041739674699220760[280] = 0;
   out_5041739674699220760[281] = 0;
   out_5041739674699220760[282] = 0;
   out_5041739674699220760[283] = 0;
   out_5041739674699220760[284] = 0;
   out_5041739674699220760[285] = 1;
   out_5041739674699220760[286] = 0;
   out_5041739674699220760[287] = 0;
   out_5041739674699220760[288] = 0;
   out_5041739674699220760[289] = 0;
   out_5041739674699220760[290] = 0;
   out_5041739674699220760[291] = 0;
   out_5041739674699220760[292] = 0;
   out_5041739674699220760[293] = 0;
   out_5041739674699220760[294] = 0;
   out_5041739674699220760[295] = 0;
   out_5041739674699220760[296] = 0;
   out_5041739674699220760[297] = 0;
   out_5041739674699220760[298] = 0;
   out_5041739674699220760[299] = 0;
   out_5041739674699220760[300] = 0;
   out_5041739674699220760[301] = 0;
   out_5041739674699220760[302] = 0;
   out_5041739674699220760[303] = 0;
   out_5041739674699220760[304] = 1;
   out_5041739674699220760[305] = 0;
   out_5041739674699220760[306] = 0;
   out_5041739674699220760[307] = 0;
   out_5041739674699220760[308] = 0;
   out_5041739674699220760[309] = 0;
   out_5041739674699220760[310] = 0;
   out_5041739674699220760[311] = 0;
   out_5041739674699220760[312] = 0;
   out_5041739674699220760[313] = 0;
   out_5041739674699220760[314] = 0;
   out_5041739674699220760[315] = 0;
   out_5041739674699220760[316] = 0;
   out_5041739674699220760[317] = 0;
   out_5041739674699220760[318] = 0;
   out_5041739674699220760[319] = 0;
   out_5041739674699220760[320] = 0;
   out_5041739674699220760[321] = 0;
   out_5041739674699220760[322] = 0;
   out_5041739674699220760[323] = 1;
}
void h_4(double *state, double *unused, double *out_5633325227063762756) {
   out_5633325227063762756[0] = state[6] + state[9];
   out_5633325227063762756[1] = state[7] + state[10];
   out_5633325227063762756[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_8034037871654296495) {
   out_8034037871654296495[0] = 0;
   out_8034037871654296495[1] = 0;
   out_8034037871654296495[2] = 0;
   out_8034037871654296495[3] = 0;
   out_8034037871654296495[4] = 0;
   out_8034037871654296495[5] = 0;
   out_8034037871654296495[6] = 1;
   out_8034037871654296495[7] = 0;
   out_8034037871654296495[8] = 0;
   out_8034037871654296495[9] = 1;
   out_8034037871654296495[10] = 0;
   out_8034037871654296495[11] = 0;
   out_8034037871654296495[12] = 0;
   out_8034037871654296495[13] = 0;
   out_8034037871654296495[14] = 0;
   out_8034037871654296495[15] = 0;
   out_8034037871654296495[16] = 0;
   out_8034037871654296495[17] = 0;
   out_8034037871654296495[18] = 0;
   out_8034037871654296495[19] = 0;
   out_8034037871654296495[20] = 0;
   out_8034037871654296495[21] = 0;
   out_8034037871654296495[22] = 0;
   out_8034037871654296495[23] = 0;
   out_8034037871654296495[24] = 0;
   out_8034037871654296495[25] = 1;
   out_8034037871654296495[26] = 0;
   out_8034037871654296495[27] = 0;
   out_8034037871654296495[28] = 1;
   out_8034037871654296495[29] = 0;
   out_8034037871654296495[30] = 0;
   out_8034037871654296495[31] = 0;
   out_8034037871654296495[32] = 0;
   out_8034037871654296495[33] = 0;
   out_8034037871654296495[34] = 0;
   out_8034037871654296495[35] = 0;
   out_8034037871654296495[36] = 0;
   out_8034037871654296495[37] = 0;
   out_8034037871654296495[38] = 0;
   out_8034037871654296495[39] = 0;
   out_8034037871654296495[40] = 0;
   out_8034037871654296495[41] = 0;
   out_8034037871654296495[42] = 0;
   out_8034037871654296495[43] = 0;
   out_8034037871654296495[44] = 1;
   out_8034037871654296495[45] = 0;
   out_8034037871654296495[46] = 0;
   out_8034037871654296495[47] = 1;
   out_8034037871654296495[48] = 0;
   out_8034037871654296495[49] = 0;
   out_8034037871654296495[50] = 0;
   out_8034037871654296495[51] = 0;
   out_8034037871654296495[52] = 0;
   out_8034037871654296495[53] = 0;
}
void h_10(double *state, double *unused, double *out_1016582291287380786) {
   out_1016582291287380786[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_1016582291287380786[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_1016582291287380786[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_5107283457947058201) {
   out_5107283457947058201[0] = 0;
   out_5107283457947058201[1] = 9.8100000000000005*cos(state[1]);
   out_5107283457947058201[2] = 0;
   out_5107283457947058201[3] = 0;
   out_5107283457947058201[4] = -state[8];
   out_5107283457947058201[5] = state[7];
   out_5107283457947058201[6] = 0;
   out_5107283457947058201[7] = state[5];
   out_5107283457947058201[8] = -state[4];
   out_5107283457947058201[9] = 0;
   out_5107283457947058201[10] = 0;
   out_5107283457947058201[11] = 0;
   out_5107283457947058201[12] = 1;
   out_5107283457947058201[13] = 0;
   out_5107283457947058201[14] = 0;
   out_5107283457947058201[15] = 1;
   out_5107283457947058201[16] = 0;
   out_5107283457947058201[17] = 0;
   out_5107283457947058201[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_5107283457947058201[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_5107283457947058201[20] = 0;
   out_5107283457947058201[21] = state[8];
   out_5107283457947058201[22] = 0;
   out_5107283457947058201[23] = -state[6];
   out_5107283457947058201[24] = -state[5];
   out_5107283457947058201[25] = 0;
   out_5107283457947058201[26] = state[3];
   out_5107283457947058201[27] = 0;
   out_5107283457947058201[28] = 0;
   out_5107283457947058201[29] = 0;
   out_5107283457947058201[30] = 0;
   out_5107283457947058201[31] = 1;
   out_5107283457947058201[32] = 0;
   out_5107283457947058201[33] = 0;
   out_5107283457947058201[34] = 1;
   out_5107283457947058201[35] = 0;
   out_5107283457947058201[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_5107283457947058201[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_5107283457947058201[38] = 0;
   out_5107283457947058201[39] = -state[7];
   out_5107283457947058201[40] = state[6];
   out_5107283457947058201[41] = 0;
   out_5107283457947058201[42] = state[4];
   out_5107283457947058201[43] = -state[3];
   out_5107283457947058201[44] = 0;
   out_5107283457947058201[45] = 0;
   out_5107283457947058201[46] = 0;
   out_5107283457947058201[47] = 0;
   out_5107283457947058201[48] = 0;
   out_5107283457947058201[49] = 0;
   out_5107283457947058201[50] = 1;
   out_5107283457947058201[51] = 0;
   out_5107283457947058201[52] = 0;
   out_5107283457947058201[53] = 1;
}
void h_13(double *state, double *unused, double *out_8039600703629375465) {
   out_8039600703629375465[0] = state[3];
   out_8039600703629375465[1] = state[4];
   out_8039600703629375465[2] = state[5];
}
void H_13(double *state, double *unused, double *out_4821764046321963694) {
   out_4821764046321963694[0] = 0;
   out_4821764046321963694[1] = 0;
   out_4821764046321963694[2] = 0;
   out_4821764046321963694[3] = 1;
   out_4821764046321963694[4] = 0;
   out_4821764046321963694[5] = 0;
   out_4821764046321963694[6] = 0;
   out_4821764046321963694[7] = 0;
   out_4821764046321963694[8] = 0;
   out_4821764046321963694[9] = 0;
   out_4821764046321963694[10] = 0;
   out_4821764046321963694[11] = 0;
   out_4821764046321963694[12] = 0;
   out_4821764046321963694[13] = 0;
   out_4821764046321963694[14] = 0;
   out_4821764046321963694[15] = 0;
   out_4821764046321963694[16] = 0;
   out_4821764046321963694[17] = 0;
   out_4821764046321963694[18] = 0;
   out_4821764046321963694[19] = 0;
   out_4821764046321963694[20] = 0;
   out_4821764046321963694[21] = 0;
   out_4821764046321963694[22] = 1;
   out_4821764046321963694[23] = 0;
   out_4821764046321963694[24] = 0;
   out_4821764046321963694[25] = 0;
   out_4821764046321963694[26] = 0;
   out_4821764046321963694[27] = 0;
   out_4821764046321963694[28] = 0;
   out_4821764046321963694[29] = 0;
   out_4821764046321963694[30] = 0;
   out_4821764046321963694[31] = 0;
   out_4821764046321963694[32] = 0;
   out_4821764046321963694[33] = 0;
   out_4821764046321963694[34] = 0;
   out_4821764046321963694[35] = 0;
   out_4821764046321963694[36] = 0;
   out_4821764046321963694[37] = 0;
   out_4821764046321963694[38] = 0;
   out_4821764046321963694[39] = 0;
   out_4821764046321963694[40] = 0;
   out_4821764046321963694[41] = 1;
   out_4821764046321963694[42] = 0;
   out_4821764046321963694[43] = 0;
   out_4821764046321963694[44] = 0;
   out_4821764046321963694[45] = 0;
   out_4821764046321963694[46] = 0;
   out_4821764046321963694[47] = 0;
   out_4821764046321963694[48] = 0;
   out_4821764046321963694[49] = 0;
   out_4821764046321963694[50] = 0;
   out_4821764046321963694[51] = 0;
   out_4821764046321963694[52] = 0;
   out_4821764046321963694[53] = 0;
}
void h_14(double *state, double *unused, double *out_5261632666550274069) {
   out_5261632666550274069[0] = state[6];
   out_5261632666550274069[1] = state[7];
   out_5261632666550274069[2] = state[8];
}
void H_14(double *state, double *unused, double *out_4070797015314811966) {
   out_4070797015314811966[0] = 0;
   out_4070797015314811966[1] = 0;
   out_4070797015314811966[2] = 0;
   out_4070797015314811966[3] = 0;
   out_4070797015314811966[4] = 0;
   out_4070797015314811966[5] = 0;
   out_4070797015314811966[6] = 1;
   out_4070797015314811966[7] = 0;
   out_4070797015314811966[8] = 0;
   out_4070797015314811966[9] = 0;
   out_4070797015314811966[10] = 0;
   out_4070797015314811966[11] = 0;
   out_4070797015314811966[12] = 0;
   out_4070797015314811966[13] = 0;
   out_4070797015314811966[14] = 0;
   out_4070797015314811966[15] = 0;
   out_4070797015314811966[16] = 0;
   out_4070797015314811966[17] = 0;
   out_4070797015314811966[18] = 0;
   out_4070797015314811966[19] = 0;
   out_4070797015314811966[20] = 0;
   out_4070797015314811966[21] = 0;
   out_4070797015314811966[22] = 0;
   out_4070797015314811966[23] = 0;
   out_4070797015314811966[24] = 0;
   out_4070797015314811966[25] = 1;
   out_4070797015314811966[26] = 0;
   out_4070797015314811966[27] = 0;
   out_4070797015314811966[28] = 0;
   out_4070797015314811966[29] = 0;
   out_4070797015314811966[30] = 0;
   out_4070797015314811966[31] = 0;
   out_4070797015314811966[32] = 0;
   out_4070797015314811966[33] = 0;
   out_4070797015314811966[34] = 0;
   out_4070797015314811966[35] = 0;
   out_4070797015314811966[36] = 0;
   out_4070797015314811966[37] = 0;
   out_4070797015314811966[38] = 0;
   out_4070797015314811966[39] = 0;
   out_4070797015314811966[40] = 0;
   out_4070797015314811966[41] = 0;
   out_4070797015314811966[42] = 0;
   out_4070797015314811966[43] = 0;
   out_4070797015314811966[44] = 1;
   out_4070797015314811966[45] = 0;
   out_4070797015314811966[46] = 0;
   out_4070797015314811966[47] = 0;
   out_4070797015314811966[48] = 0;
   out_4070797015314811966[49] = 0;
   out_4070797015314811966[50] = 0;
   out_4070797015314811966[51] = 0;
   out_4070797015314811966[52] = 0;
   out_4070797015314811966[53] = 0;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_5382296959486538598) {
  err_fun(nom_x, delta_x, out_5382296959486538598);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_1423671362174335144) {
  inv_err_fun(nom_x, true_x, out_1423671362174335144);
}
void pose_H_mod_fun(double *state, double *out_6640898992211347549) {
  H_mod_fun(state, out_6640898992211347549);
}
void pose_f_fun(double *state, double dt, double *out_5710795834153600449) {
  f_fun(state,  dt, out_5710795834153600449);
}
void pose_F_fun(double *state, double dt, double *out_5041739674699220760) {
  F_fun(state,  dt, out_5041739674699220760);
}
void pose_h_4(double *state, double *unused, double *out_5633325227063762756) {
  h_4(state, unused, out_5633325227063762756);
}
void pose_H_4(double *state, double *unused, double *out_8034037871654296495) {
  H_4(state, unused, out_8034037871654296495);
}
void pose_h_10(double *state, double *unused, double *out_1016582291287380786) {
  h_10(state, unused, out_1016582291287380786);
}
void pose_H_10(double *state, double *unused, double *out_5107283457947058201) {
  H_10(state, unused, out_5107283457947058201);
}
void pose_h_13(double *state, double *unused, double *out_8039600703629375465) {
  h_13(state, unused, out_8039600703629375465);
}
void pose_H_13(double *state, double *unused, double *out_4821764046321963694) {
  H_13(state, unused, out_4821764046321963694);
}
void pose_h_14(double *state, double *unused, double *out_5261632666550274069) {
  h_14(state, unused, out_5261632666550274069);
}
void pose_H_14(double *state, double *unused, double *out_4070797015314811966) {
  H_14(state, unused, out_4070797015314811966);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
