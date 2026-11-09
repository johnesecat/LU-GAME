use bevy::prelude::*;
use std::collections::HashMap;

/// Parsed game data tables loaded from assets/data/tables.json + dialogue.
#[derive(Resource, Default)]
pub struct Tables {
    pub positions: Vec<(String, String)>,          // (id, display)
    pub scalars: Vec<(String, String, f32, f32, f32)>, // (id, display, default, min, max)
    pub booleans: Vec<(String, String, bool)>,     // (id, display, default)
    pub env_colors: Vec<(String, String, [f32; 4])>,
    pub dialogue: HashMap<String, Vec<String>>,     // event -> lines
    pub stringtables: HashMap<String, String>,
}

#[derive(serde::Deserialize)]
struct TablesRaw {
    #[serde(default)]
    session_scalars: Vec<RowScalar>,
    #[serde(default)]
    session_booleans: Vec<RowBool>,
    #[serde(default)]
    positions: Vec<RowScalar>,
    #[serde(default)]
    env_colors: Vec<RowScalar>,
}

#[derive(serde::Deserialize)]
struct RowScalar {
    id: String,
    display: Option<String>,
    #[serde(default)]
    default: Option<f32>,
    #[serde(default)]
    min: Option<f32>,
    #[serde(default)]
    max: Option<f32>,
}

#[derive(serde::Deserialize)]
struct RowBool {
    id: String,
    display: Option<String>,
    #[serde(default)]
    value: Option<bool>,
}

impl Tables {
    pub fn load(json: &str, dialogue_txt: &str) -> Self {
        let raw: TablesRaw = serde_json::from_str(json).unwrap_or(TablesRaw {
            session_scalars: vec![],
            session_booleans: vec![],
            positions: vec![],
            env_colors: vec![],
        });
        let mut t = Tables::default();
        for r in raw.session_scalars {
            t.scalars.push((r.id, r.display.unwrap_or_default(),
                            r.default.unwrap_or(0.0), r.min.unwrap_or(0.0), r.max.unwrap_or(1.0)));
        }
        for r in raw.session_booleans {
            t.booleans.push((r.id, r.display.unwrap_or_default(), r.value.unwrap_or(false)));
        }
        for r in raw.positions {
            t.positions.push((r.id, r.display.unwrap_or_default()));
        }
        for r in raw.env_colors {
            t.env_colors.push((r.id, r.display.unwrap_or_default(), [0.5, 0.5, 0.5, 1.0]));
        }
        // parse dialogue: lines like  event:"text"
        for line in dialogue_txt.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with("dialogue_name") { continue; }
            if let Some((k, v)) = line.split_once(':') {
                let key = k.trim().trim_matches('"').to_string();
                let val = v.trim().trim_matches('"')
                    .replace("* NAME*", "Master")
                    .replace("*NAME*", "Master")
                    .replace("*FINISHES*", "that");
                t.dialogue.entry(key).or_default().push(val);
            }
        }
        t
    }
}
