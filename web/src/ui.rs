use bevy::prelude::*;

#[derive(Component)]
pub struct ArousalMeter;

pub fn meter_update(
    session: Res<crate::gameplay::Session>,
    dlg: Res<crate::gameplay::DialogueState>,
    mut q: Query<&mut Text, With<ArousalMeter>>,
) {
    for mut text in &mut q {
        let pct = (session.arousal * 100.0) as u32;
        let line = if let Some((t, _)) = &dlg.current {
            format!("{}\n\nArousal: {}%", t, pct)
        } else {
            format!("Arousal: {}%", pct)
        };
        text.sections[0].value = line;
    }
}
