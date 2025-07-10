#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void live_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_9(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_12(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_35(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_32(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_33(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_H(double *in_vec, double *out_7600010581399056782);
void live_err_fun(double *nom_x, double *delta_x, double *out_9093486101329025161);
void live_inv_err_fun(double *nom_x, double *true_x, double *out_2394738032955467188);
void live_H_mod_fun(double *state, double *out_4197737053259762491);
void live_f_fun(double *state, double dt, double *out_5773040843365799752);
void live_F_fun(double *state, double dt, double *out_7014037893130285203);
void live_h_4(double *state, double *unused, double *out_5370307516932246012);
void live_H_4(double *state, double *unused, double *out_5638175795716657566);
void live_h_9(double *state, double *unused, double *out_4016366934518024377);
void live_H_9(double *state, double *unused, double *out_5879365442346248211);
void live_h_10(double *state, double *unused, double *out_8719325861670657530);
void live_H_10(double *state, double *unused, double *out_8230897453765926573);
void live_h_12(double *state, double *unused, double *out_2842053904946923373);
void live_H_12(double *state, double *unused, double *out_7789111869960932255);
void live_h_35(double *state, double *unused, double *out_5412374249492348822);
void live_H_35(double *state, double *unused, double *out_9004837853089264942);
void live_h_32(double *state, double *unused, double *out_1032690796440585336);
void live_H_32(double *state, double *unused, double *out_6118356430240810446);
void live_h_13(double *state, double *unused, double *out_535570663572175509);
void live_H_13(double *state, double *unused, double *out_6858680272735146732);
void live_h_14(double *state, double *unused, double *out_4016366934518024377);
void live_H_14(double *state, double *unused, double *out_5879365442346248211);
void live_h_33(double *state, double *unused, double *out_7887278980270050598);
void live_H_33(double *state, double *unused, double *out_6291349215981429070);
void live_predict(double *in_x, double *in_P, double *in_Q, double dt);
}