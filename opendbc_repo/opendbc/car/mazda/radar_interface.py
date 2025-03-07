#!/usr/bin/env python3
from opendbc.car.interfaces import RadarInterfaceBase
from opendbc.car.mazda.values import CAR, MazdaFlags
from opendbc.can.parser import CANParser
import numpy as np

class RadarInterface(RadarInterfaceBase):
  """
  Mazda radar interface

  Note: Most Mazda models don't have direct access to radar data and rely on vision system.
  For CX5 2022 model, we can access radar data through standard CAN bus to provide better lead tracking.
  This implementation uses the stock radar hardware, no third-party hardware is required.
  """
  def __init__(self, CP):
    super().__init__()
    self.CP = CP

    # Check if car is CX5 2022 with radar support
    self.is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022
    self.has_radar = self.is_cx5_2022 and CP.flags & 2

    # Initialize radar tracks
    self.track_id = 0
    self.radar_tracks = {}
    self.radar_ts_last = 0.0

    # Create radar parser if supported
    self.radar_parser = None
    if self.has_radar:
      self.radar_parser = self._create_radar_parser()

  def _create_radar_parser(self):
    """Create radar parser for CX5 2022 using standard hardware"""
    if not self.has_radar:
      return None

    # Define radar signals to parse from standard CAN bus
    radar_signals = []

    # Add all radar track signals from stock radar
    for i in range(1, 7):  # 6 radar tracks
      track_msg = f"RADAR_TRACK_36{i}"
      radar_signals.extend([
        (track_msg, "STATUS"),
        (track_msg, "DIST_OBJ"),
        (track_msg, "RELV_OBJ"),
        (track_msg, "ANG_OBJ"),
      ])

    # Create parser for standard radar bus
    return CANParser("mazda_radar", radar_signals, [], 1)

  def update(self, can_strings):
    """
    Update radar data

    Args:
        can_strings: CAN messages

    Returns:
        RadarData object
    """
    # If not CX5 2022 with radar support, return empty radar data
    if not self.has_radar or self.radar_parser is None:
      return super().update(can_strings)

    # Update radar parser with new CAN messages
    radar_data = self._update_radar_data(can_strings)
    return radar_data

  def _update_radar_data(self, can_strings):
    """
    Parse radar data from CAN messages

    Args:
        can_strings: CAN messages

    Returns:
        RadarData object with parsed radar tracks
    """
    if self.radar_parser is None:
      return super().update(can_strings)

    # Parse radar messages
    vls = self.radar_parser.update_strings(can_strings)

    # Initialize radar data
    ret = super().update(can_strings)

    # Process each radar track
    for i in range(1, 7):  # 6 radar tracks
      track_msg = f"RADAR_TRACK_36{i}"

      if track_msg in vls:
        # Get track status
        status = vls[track_msg].get("STATUS", 0)

        # Status 3+ indicates confident detection
        if status >= 3:
          # Get track data
          dist = vls[track_msg].get("DIST_OBJ", 0)
          rel_speed = vls[track_msg].get("RELV_OBJ", 0)
          angle = vls[track_msg].get("ANG_OBJ", 0)

          # Validate distance
          if 0.1 < dist < 150.0:
            # Convert to meters and m/s
            dist_m = dist
            rel_speed_m = rel_speed

            # Calculate lateral distance
            lat_dist = np.sin(np.radians(angle)) * dist_m

            # Create radar point
            ret.points.append({
              "trackId": i,
              "dRel": float(dist_m),
              "yRel": float(lat_dist),
              "vRel": float(rel_speed_m),
              "aRel": 0.0,
              "yvRel": 0.0,
              "measured": True,
            })

    return ret
