use bevy::prelude::*;

/// Session state — mirrors the game's session data tables.
#[derive(Resource)]
pub struct Session {
    pub position: usize,        // index into positions
    pub depth: f32,            // 0..1 penetration depth
    pub speed: f32,             // stroke speed
    pub arousal: f32,           // 0..1
    pub finishes: u32,
    pub auto_mode: bool,
    pub auto_speed: f32,
    pub auto_passion: f32,
    pub auto_force: f32,
    pub control_balance: f32,
    pub env_color: usize,
    pub elapsed: f32,
    pub stroke_phase: f32,
}

impl Default for Session {
    fn default() -> Self {
        Self {
            position: 0,
            depth: 0.0,
            speed: 0.0,
            arousal: 0.0,
            finishes: 0,
            auto_mode: false,
            auto_speed: 0.5,
            auto_passion: 0.5,
            auto_force: 0.5,
            control_balance: 0.5,
            env_color: 0,
            elapsed: 0.0,
            stroke_phase: 0.0,
        }
    }
}

#[derive(Resource)]
pub struct DialogueState {
    pub current: Option<(String, f32)>, // (text, time remaining)
    pub frequency: f32,
    pub last_event: String,
    pub cooldown: f32,
}

impl Default for DialogueState {
    fn default() -> Self {
        Self { current: None, frequency: 0.5, last_event: String::new(), cooldown: 0.0 }
    }
}

pub fn session_update(
    time: Res<Time>,
    mut session: ResMut<Session>,
    stroke: Res<crate::input::StrokeInput>,
    mut dialogue: ResMut<DialogueState>,
) {
    let dt = time.delta_seconds();
    session.elapsed += dt;

    // stroke dynamics: velocity from input, depth follows
    if stroke.active {
        session.stroke_phase += dt * (1.0 + session.speed * 3.0);
        let target_depth = (stroke.value * 0.5 + 0.5).clamp(0.0, 1.0);
        session.depth += (target_depth - session.depth) * (dt * 8.0).min(1.0);
        session.speed = (session.speed + dt * 0.5).min(2.0);
    } else {
        session.speed = (session.speed - dt * 0.8).max(0.0);
        if session.auto_mode {
            // auto mode: sinusoidal stroke
            session.stroke_phase += dt * (0.5 + session.auto_speed * 2.0);
            session.depth = 0.5 + 0.5 * (session.stroke_phase * std::f32::consts::TAU).sin()
                * (0.3 + session.auto_force * 0.7);
        }
    }

    // arousal grows with depth * speed
    let stimulation = session.depth * (0.3 + session.speed * 0.7);
    session.arousal = (session.arousal + stimulation * dt * 0.1).min(1.0);

    // dialogue cooldown
    if dialogue.cooldown > 0.0 {
        dialogue.cooldown -= dt;
    }
    if let Some((_, t)) = &mut dialogue.current {
        *t -= dt;
        if *t <= 0.0 {
            dialogue.current = None;
        }
    }
}

pub fn dialogue_update(
    session: Res<Session>,
    mut dlg: ResMut<DialogueState>,
    tables: Option<Res<crate::data::Tables>>,
) {
    let Some(tables) = tables else { return };
    if dlg.current.is_some() || dlg.cooldown > 0.0 { return; }
    if session.arousal < 0.15 { return; }

    // pick a dialogue event based on state
    let event = if session.depth > 0.95 {
        "first_dt"
    } else if session.depth > 0.7 {
        "first_throat"
    } else if session.speed > 1.2 {
        "vigorous"
    } else {
        return;
    };
    if dlg.last_event == event && session.elapsed < 10.0 { return; }

    if let Some(lines) = tables.dialogue.get(event) {
        if !lines.is_empty() {
            let idx = (session.elapsed * 7.0) as usize % lines.len();
            dlg.current = Some((lines[idx].clone(), 3.0));
            dlg.last_event = event.to_string();
            dlg.cooldown = 4.0 / (0.1 + dlg.frequency);
        }
    }
}
