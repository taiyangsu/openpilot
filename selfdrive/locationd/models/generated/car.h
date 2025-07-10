#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_8158352025397144018);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_3840507356042869356);
void car_H_mod_fun(double *state, double *out_8812957270946793058);
void car_f_fun(double *state, double dt, double *out_650578715203675723);
void car_F_fun(double *state, double dt, double *out_6055581464108427346);
void car_h_25(double *state, double *unused, double *out_7242435212238372235);
void car_H_25(double *state, double *unused, double *out_6539768529970362050);
void car_h_24(double *state, double *unused, double *out_9219157191433753894);
void car_H_24(double *state, double *unused, double *out_2688296656098833175);
void car_h_30(double *state, double *unused, double *out_7085248543887243090);
void car_H_30(double *state, double *unused, double *out_7379279213611581368);
void car_h_26(double *state, double *unused, double *out_2236309562360665869);
void car_H_26(double *state, double *unused, double *out_8165472224865133342);
void car_h_27(double *state, double *unused, double *out_2118302168427289125);
void car_H_27(double *state, double *unused, double *out_5204515901811156457);
void car_h_29(double *state, double *unused, double *out_7688564428563720607);
void car_H_29(double *state, double *unused, double *out_7889510557925973552);
void car_h_28(double *state, double *unused, double *out_1136218075091991013);
void car_H_28(double *state, double *unused, double *out_2807111540856442978);
void car_h_31(double *state, double *unused, double *out_4241589905187600354);
void car_H_31(double *state, double *unused, double *out_7539264122631781866);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}