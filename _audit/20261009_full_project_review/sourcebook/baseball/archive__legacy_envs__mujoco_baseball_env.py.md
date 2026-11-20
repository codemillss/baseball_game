# baseball/archive/legacy_envs/mujoco_baseball_env.py

원본: [archive/legacy_envs/mujoco_baseball_env.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_envs/mujoco_baseball_env.py)

SHA256: `54f365bdac3311eee1d5a996cad0fa1093c0136c38fabce2f2e6886192f1cef0`

전체 243행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `MuJoCoBaseballEnv` | ClassDef | 22 | 243 |
| `__init__` | FunctionDef | 27 | 74 |
| `_get_obs` | FunctionDef | 76 | 94 |
| `reset` | FunctionDef | 96 | 133 |
| `step` | FunctionDef | 135 | 158 |
| `_apply_aerodynamics` | FunctionDef | 160 | 175 |
| `_check_contacts` | FunctionDef | 177 | 203 |
| `_compute_reward_and_done` | FunctionDef | 205 | 231 |
| `render` | FunctionDef | 233 | 238 |
| `close` | FunctionDef | 240 | 243 |

## 전체 원문

````text
    1 | """
    2 | mujoco_baseball_env.py — High-Res 3D MuJoCo Baseball Physics Environment
    3 | 
    4 | MuJoCo 3.x + Gymnasium 래퍼 환경:
    5 | - 3D Stadium Field (마운드, 베이스, 펜스, 스트라이크 존)
    6 | - 3D Dynamic Baseball (Freejoint + Drag/Magnus Air Resistance)
    7 | - Multi-DOF Articulated Bat (Torque / Joint Control)
    8 | - Contact & Hit Dynamics (Exit Velocity, Launch Angle, Spray Angle)
    9 | """
   10 | 
   11 | import os
   12 | from pathlib import Path
   13 | from typing import Optional, Dict, Tuple, Any
   14 | 
   15 | import numpy as np
   16 | import gymnasium as gym
   17 | from gymnasium import spaces
   18 | 
   19 | import mujoco
   20 | 
   21 | 
   22 | class MuJoCoBaseballEnv(gym.Env):
   23 |     """3D MuJoCo 야구 시뮬레이션 Gymnasium 환경."""
   24 | 
   25 |     metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 60}
   26 | 
   27 |     def __init__(
   28 |         self,
   29 |         xml_path: Optional[str] = None,
   30 |         frame_skip: int = 5,
   31 |         render_mode: Optional[str] = None,
   32 |     ):
   33 |         super().__init__()
   34 | 
   35 |         if xml_path is None:
   36 |             xml_path = str(Path(__file__).parent.parent / "assets" / "stadium_3d.xml")
   37 | 
   38 |         if not os.path.exists(xml_path):
   39 |             raise FileNotFoundError(f"MuJoCo XML file not found at: {xml_path}")
   40 | 
   41 |         self.xml_path = xml_path
   42 |         self.model = mujoco.MjModel.from_xml_path(self.xml_path)
   43 |         self.data = mujoco.MjData(self.model)
   44 |         self.frame_skip = frame_skip
   45 |         self.render_mode = render_mode
   46 | 
   47 |         # ID 캐싱
   48 |         self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
   49 |         self.bat_base_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "bat_base")
   50 |         self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
   51 |         self.bat_barrel_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
   52 | 
   53 |         # Action Space: [Bat Yaw Torque, Bat Pitch Torque, Bat Roll Torque] [-1, 1]
   54 |         self.action_space = spaces.Box(
   55 |             low=-1.0, high=1.0, shape=(3,), dtype=np.float32
   56 |         )
   57 | 
   58 |         # Observation Space:
   59 |         # [ball_pos(3), ball_vel(3), bat_qpos(3), bat_qvel(3), rel_dist(3)] -> 15차원
   60 |         obs_low = np.array([-100.0] * 15, dtype=np.float32)
   61 |         obs_high = np.array([100.0] * 15, dtype=np.float32)
   62 |         self.observation_space = spaces.Box(low=obs_low, high=obs_high, dtype=np.float32)
   63 | 
   64 |         # 렌더러 초기화 (비디오 / 시각화용)
   65 |         self.renderer = None
   66 |         if self.render_mode == "rgb_array":
   67 |             self.renderer = mujoco.Renderer(self.model, height=480, width=640)
   68 | 
   69 |         # 상태 제어 변수
   70 |         self.step_count = 0
   71 |         self.max_steps = 200
   72 |         self.has_contacted = False
   73 |         self.max_exit_velocity = 0.0
   74 |         self.hit_info = {}
   75 | 
   76 |     def _get_obs(self) -> np.ndarray:
   77 |         """현재 3D 물리 상태에서 관찰 벡터를 추출합니다."""
   78 |         # 공 위치 & 속도 (qpos 0:3, qvel 0:3 for freejoint)
   79 |         ball_pos = self.data.xpos[self.ball_body_id].copy()
   80 |         ball_vel = self.data.cvel[self.ball_body_id][3:6].copy()
   81 | 
   82 |         # 배트 관절 각도 & 각속도 (bat joints: index 1, 2, 3 in model joints)
   83 |         bat_qpos = self.data.qpos[7:10].copy()  # 0~6: ball freejoint (pos3 + quat4)
   84 |         bat_qvel = self.data.qvel[6:9].copy()  # 0~5: ball freejoint (vel3 + rot3)
   85 | 
   86 |         # 상대 위치 벡터
   87 |         bat_pos = self.data.xpos[self.bat_base_id].copy()
   88 |         rel_dist = ball_pos - bat_pos
   89 | 
   90 |         obs = np.concatenate([
   91 |             ball_pos, ball_vel, bat_qpos, bat_qvel, rel_dist
   92 |         ], dtype=np.float32)
   93 | 
   94 |         return obs
   95 | 
   96 |     def reset(
   97 |         self,
   98 |         *,
   99 |         seed: Optional[int] = None,
  100 |         options: Optional[dict] = None,
  101 |     ) -> Tuple[np.ndarray, Dict[str, Any]]:
  102 |         """환경 초기화: 투수 마운드에서 공 투구."""
  103 |         super().reset(seed=seed)
  104 | 
  105 |         mujoco.mj_resetData(self.model, self.data)
  106 | 
  107 |         # 1. 야구공 초기 위치 (마운드: x=0, y=18.44, z=1.8)
  108 |         self.data.qpos[0] = self.np_random.uniform(-0.1, 0.1)  # x 약간 유인
  109 |         self.data.qpos[1] = 18.44                               # y 마운드
  110 |         self.data.qpos[2] = 1.8 + self.np_random.uniform(-0.05, 0.05)  # z 릴리스 높이
  111 |         self.data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]             # 쿼터니언
  112 | 
  113 |         # 2. 투구 초기 속도 (예: 130 ~ 150 km/h -> 36.1 ~ 41.6 m/s)
  114 |         v_y = -self.np_random.uniform(36.0, 42.0)
  115 |         v_x = self.np_random.uniform(-1.0, 1.0)
  116 |         v_z = self.np_random.uniform(-1.0, 1.5)
  117 |         self.data.qvel[0] = v_x
  118 |         self.data.qvel[1] = v_y
  119 |         self.data.qvel[2] = v_z
  120 | 
  121 |         # 3. 배트 초기 위치 초기화
  122 |         self.data.qpos[7:10] = 0.0
  123 |         self.data.qvel[6:9] = 0.0
  124 | 
  125 |         mujoco.mj_forward(self.model, self.data)
  126 | 
  127 |         self.step_count = 0
  128 |         self.has_contacted = False
  129 |         self.max_exit_velocity = 0.0
  130 |         self.hit_info = {}
  131 | 
  132 |         obs = self._get_obs()
  133 |         return obs, {}
  134 | 
  135 |     def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
  136 |         """물리 프레임 진행 및 보상 계산."""
  137 |         action = np.clip(action, -1.0, 1.0)
  138 | 
  139 |         # 액션 적용 (Motor ctrl)
  140 |         self.data.ctrl[0] = action[0] * 100.0  # yaw torque
  141 |         self.data.ctrl[1] = action[1] * 50.0   # pitch torque
  142 |         self.data.ctrl[2] = action[2] * 50.0   # roll torque
  143 | 
  144 |         # Frame skip 물리 스텝
  145 |         for _ in range(self.frame_skip):
  146 |             # 공기저항 & 마그누스 양력 보정
  147 |             self._apply_aerodynamics()
  148 |             mujoco.mj_step(self.model, self.data)
  149 |             self._check_contacts()
  150 | 
  151 |         self.step_count += 1
  152 |         obs = self._get_obs()
  153 | 
  154 |         # 보상 계산 및 종료 조건 검사
  155 |         reward, terminated, info = self._compute_reward_and_done()
  156 |         truncated = self.step_count >= self.max_steps
  157 | 
  158 |         return obs, reward, terminated, truncated, info
  159 | 
  160 |     def _apply_aerodynamics(self):
  161 |         """공기저항(Drag) 및 마그누스(Magnus) 양력을 공에 부과합니다."""
  162 |         ball_vel = self.data.cvel[self.ball_body_id][3:6]
  163 |         speed = np.linalg.norm(ball_vel)
  164 |         if speed < 1e-3:
  165 |             return
  166 | 
  167 |         # 항력 Cd = 0.3
  168 |         rho = 1.225
  169 |         area = np.pi * (0.037 ** 2)
  170 |         c_d = 0.3
  171 |         drag_mag = 0.5 * rho * (speed ** 2) * area * c_d
  172 |         drag_force = -drag_mag * (ball_vel / speed)
  173 | 
  174 |         # xfrc_applied에 외력 추가 (freejoint body index)
  175 |         self.data.xfrc_applied[self.ball_body_id][:3] = drag_force
  176 | 
  177 |     def _check_contacts(self):
  178 |         """배트와 야구공 간의 충돌 여부를 감지합니다."""
  179 |         for i in range(self.data.ncon):
  180 |             con = self.data.contact[i]
  181 |             g1, g2 = con.geom1, con.geom2
  182 | 
  183 |             is_ball = (g1 == self.ball_geom_id or g2 == self.ball_geom_id)
  184 |             is_bat = (g1 == self.bat_barrel_id or g2 == self.bat_barrel_id)
  185 | 
  186 |             if is_ball and is_bat:
  187 |                 self.has_contacted = True
  188 |                 ball_vel = self.data.cvel[self.ball_body_id][3:6]
  189 |                 exit_speed_kmh = np.linalg.norm(ball_vel) * 3.6
  190 |                 if exit_speed_kmh > self.max_exit_velocity:
  191 |                     self.max_exit_velocity = exit_speed_kmh
  192 | 
  193 |                     # 발사각 & 스프레이각 추정
  194 |                     vx, vy, vz = ball_vel
  195 |                     horiz_speed = np.hypot(vx, vy)
  196 |                     launch_angle = np.degrees(np.arctan2(vz, max(horiz_speed, 1e-3)))
  197 |                     spray_angle = np.degrees(np.arctan2(vx, max(-vy, 1e-3)))
  198 | 
  199 |                     self.hit_info = {
  200 |                         'exit_velocity_kmh': exit_speed_kmh,
  201 |                         'launch_angle': launch_angle,
  202 |                         'spray_angle': spray_angle,
  203 |                     }
  204 | 
  205 |     def _compute_reward_and_done(self) -> Tuple[float, bool, Dict[str, Any]]:
  206 |         """보상 함수 및 종료 여부 산출."""
  207 |         ball_pos = self.data.xpos[self.ball_body_id]
  208 |         reward = 0.0
  209 |         terminated = False
  210 |         info = {'has_contacted': self.has_contacted, **self.hit_info}
  211 | 
  212 |         # 1. Contact Reward
  213 |         if self.has_contacted:
  214 |             reward += 10.0
  215 |             # 2. Exit Velocity Reward
  216 |             reward += (self.max_exit_velocity / 10.0)
  217 | 
  218 |             # 3. Fair Zone Angle Reward (-45도 ~ +45도 페어)
  219 |             sa = self.hit_info.get('spray_angle', 0.0)
  220 |             if -45.0 <= sa <= 45.0:
  221 |                 reward += 5.0  # Fair zone bonus
  222 | 
  223 |             terminated = True
  224 | 
  225 |         # 공이 캐처 미트 통과 (y < -0.5) 또는 바닥 낙하 (z < 0.1)
  226 |         elif ball_pos[1] < -0.5 or ball_pos[2] < 0.05:
  227 |             # 접촉 못하고 통과함 -> 스트라이크/볼
  228 |             reward -= 1.0
  229 |             terminated = True
  230 | 
  231 |         return float(reward), terminated, info
  232 | 
  233 |     def render(self) -> Optional[np.ndarray]:
  234 |         """3D 프레임 렌더링."""
  235 |         if self.renderer is not None:
  236 |             self.renderer.update_scene(self.data)
  237 |             return self.renderer.render()
  238 |         return None
  239 | 
  240 |     def close(self):
  241 |         """환경 닫기."""
  242 |         if self.renderer is not None:
  243 |             del self.renderer
````
