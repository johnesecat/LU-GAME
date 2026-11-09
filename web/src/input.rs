use bevy::prelude::*;
use bevy::input::touch::TouchPhase;

/// Touch drag input for mobile Safari: one finger = stroke control.
#[derive(Resource, Default)]
pub struct StrokeInput {
    pub value: f32,      // -1..1 current stroke position
    pub velocity: f32,   // stroke velocity
    pub active: bool,
}

pub fn touch_drag(
    mut touch_evr: EventReader<TouchInput>,
    mut stroke: ResMut<StrokeInput>,
    windows: Query<&Window>,
) {
    let Ok(window) = windows.get_single() else { return };
    for ev in touch_evr.read() {
        match ev.phase {
            TouchPhase::Started => {
                stroke.active = true;
            }
            TouchPhase::Moved => {
                let h = window.height();
                let y = ev.position.y;
                stroke.value = ((y / h) * 2.0 - 1.0).clamp(-1.0, 1.0);
            }
            TouchPhase::Ended | TouchPhase::Canceled => {
                stroke.active = false;
            }
        }
    }
}

pub fn mouse_drag(
    buttons: Res<ButtonInput<MouseButton>>,
    mut stroke: ResMut<StrokeInput>,
    windows: Query<&Window>,
    keys: Res<ButtonInput<KeyCode>>,
) {
    let Ok(window) = windows.get_single() else { return };
    let mut kv = 0.0;
    if keys.pressed(KeyCode::KeyW) || keys.pressed(KeyCode::ArrowUp) { kv -= 1.0; }
    if keys.pressed(KeyCode::KeyS) || keys.pressed(KeyCode::ArrowDown) { kv += 1.0; }
    if kv != 0.0 {
        stroke.value = (stroke.value + kv * 0.05).clamp(-1.0, 1.0);
        stroke.active = true;
        return;
    }
    if buttons.pressed(MouseButton::Left) {
        if let Some(p) = window.cursor_position() {
            let h = window.height();
            stroke.value = ((p.y / h) * 2.0 - 1.0).clamp(-1.0, 1.0);
            stroke.active = true;
        }
    } else {
        stroke.active = false;
    }
}
