use bevy::prelude::*;
use bevy::input::touch::TouchPhase;
use bevy::render::mesh::{Indices, VertexAttributeValues};
use bevy::render::render_resource::PrimitiveTopology;

pub mod data;
pub mod gameplay;
pub mod input;
pub mod ui;

#[derive(States, Debug, Clone, PartialEq, Eq, Hash, Default)]
pub enum GameState {
    #[default]
    Loading,
    Menu,
    Playing,
    Paused,
}

#[derive(Resource)]
pub struct CharacterMesh {
    pub positions: Vec<[f32; 3]>,
    pub uvs: Vec<[f32; 2]>,
    pub indices: Vec<u32>,
}

impl CharacterMesh {
    pub fn load(bin: &[u8]) -> Option<Self> {
        if bin.len() < 8 { return None; }
        let vc = u32::from_le_bytes(bin[0..4].try_into().ok()?) as usize;
        let ic = u32::from_le_bytes(bin[4..8].try_into().ok()?) as usize;
        if bin.len() < 8 + vc*20 + ic*4 { return None; }
        let mut positions = Vec::with_capacity(vc);
        let mut uvs = Vec::with_capacity(vc);
        let mut p = 8;
        for _ in 0..vc {
            let x = f32::from_le_bytes(bin[p..p+4].try_into().ok()?);
            let y = f32::from_le_bytes(bin[p+4..p+8].try_into().ok()?);
            let z = f32::from_le_bytes(bin[p+8..p+12].try_into().ok()?);
            positions.push([x, y, z]);
            p += 12;
        }
        for _ in 0..vc {
            let u = f32::from_le_bytes(bin[p..p+4].try_into().ok()?);
            let v = f32::from_le_bytes(bin[p+4..p+8].try_into().ok()?);
            uvs.push([u, v]);
            p += 8;
        }
        let mut indices = Vec::with_capacity(ic);
        for _ in 0..ic {
            indices.push(u32::from_le_bytes(bin[p..p+4].try_into().ok()?));
            p += 4;
        }
        Some(Self { positions, uvs, indices })
    }

    pub fn to_bevy_mesh(&self) -> Mesh {
        let mut m = Mesh::new(PrimitiveTopology::TriangleList, bevy::render::render_asset::RenderAssetUsages::default());
        m.insert_attribute(
            Mesh::ATTRIBUTE_POSITION,
            VertexAttributeValues::Float32x3(self.positions.clone()),
        );
        m.insert_attribute(
            Mesh::ATTRIBUTE_UV_0,
            VertexAttributeValues::Float32x2(self.uvs.clone()),
        );
        let mut normals = vec![[0.0f32; 3]; self.positions.len()];
        for tri in self.indices.chunks(3) {
            if tri.len() == 3 {
                let a = self.positions[tri[0] as usize];
                let b = self.positions[tri[1] as usize];
                let c = self.positions[tri[2] as usize];
                let e1 = [b[0]-a[0], b[1]-a[1], b[2]-a[2]];
                let e2 = [c[0]-a[0], c[1]-a[1], c[2]-a[2]];
                let n = [e1[1]*e2[2]-e1[2]*e2[1], e1[2]*e2[0]-e1[0]*e2[2], e1[0]*e2[1]-e1[1]*e2[0]];
                for &i in tri {
                    let ni = &mut normals[i as usize];
                    ni[0] += n[0]; ni[1] += n[1]; ni[2] += n[2];
                }
            }
        }
        for n in normals.iter_mut() {
            let l = (n[0]*n[0] + n[1]*n[1] + n[2]*n[2]).sqrt().max(1e-8);
            *n = [n[0]/l, n[1]/l, n[2]/l];
        }
        m.insert_attribute(
            Mesh::ATTRIBUTE_NORMAL,
            VertexAttributeValues::Float32x3(normals),
        );
        m.insert_indices(Indices::U32(self.indices.clone()));
        m
    }
}

#[derive(Resource)]
pub struct CharacterMeshLoaded(pub CharacterMesh);

#[derive(Resource)]
pub struct PenisMeshLoaded(pub CharacterMesh);

#[derive(Resource)]
pub struct MaidMeshLoaded(pub CharacterMesh);

#[derive(Component)]
pub struct CharacterMarker;

#[derive(Component)]
pub struct PenisMarker;

#[derive(Component)]
pub struct MaidMarker;

pub fn run() {
    App::new()
        .add_plugins(DefaultPlugins
            .set(WindowPlugin {
                primary_window: Some(Window {
                    title: "HyperDeep".to_string(),
                    fit_canvas_to_parent: true,
                    prevent_default_event_handling: true,
                    ..default()
                }),
                ..default()
            })
            .set(ImagePlugin::default_nearest()))
        .init_state::<GameState>()
        .insert_resource(gameplay::Session::default())
        .insert_resource(gameplay::DialogueState::default())
        .insert_resource(input::StrokeInput::default())
        .add_systems(Startup, (load_data, spawn_scene, spawn_ui))
        .add_systems(Update, (
            input::touch_drag,
            input::mouse_drag,
            gameplay::session_update,
            gameplay::dialogue_update,
            ui::meter_update,
            animate_character,
            animate_penis,
        ).run_if(in_state(GameState::Playing)))
        .run();
}

fn load_data(mut commands: Commands) {
    let tables = data::Tables::load(
        include_str!("../assets/data/tables.json"),
        include_str!("../../HDT/Content/Dialogue/default.txt"),
    );
    info!("loaded {} positions, {} scalars, {} dialogue events",
          tables.positions.len(), tables.scalars.len(), tables.dialogue.len());
    commands.insert_resource(tables);
    let mesh = CharacterMesh::load(include_bytes!("../assets/meshes/hdchan_lod0.bin"));
    match mesh {
        Some(m) => { info!("mesh: {} verts", m.positions.len()); commands.insert_resource(CharacterMeshLoaded(m)); }        None => error!("mesh load failed"),
    }
    let penis = CharacterMesh::load(include_bytes!("../assets/meshes/characters/dude/dick/materials/standard/sm_dude_dick.bin"));
    match penis {
        Some(m) => { info!("penis mesh: {} verts", m.positions.len()); commands.insert_resource(PenisMeshLoaded(m)); }
        None => {
            let pop = CharacterMesh::load(include_bytes!("../assets/meshes/characters/dude/dick/materials/popsicle/dude_popsicle.bin"));
            match pop {
                Some(m) => { info!("popsicle mesh: {} verts", m.positions.len()); commands.insert_resource(PenisMeshLoaded(m)); }
                        None => error!("penis+popsicle mesh load failed"),
            }
        }
    }
    let maid = CharacterMesh::load(include_bytes!("../assets/meshes/characters/hdchan/clothing/items/dresses/maid/sm_maid-dress.bin"));
    match maid {
        Some(m) => { info!("maid dress mesh: {} verts", m.positions.len()); commands.insert_resource(MaidMeshLoaded(m)); }
        None => error!("maid mesh load failed"),
    }
}

fn spawn_scene(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
    asset_server: Res<AssetServer>,
    mesh_res: Option<Res<CharacterMeshLoaded>>,
    penis_res: Option<Res<PenisMeshLoaded>>,
    maid_res: Option<Res<MaidMeshLoaded>>,
) {
    commands.spawn(PbrBundle {
        mesh: meshes.add(Plane3d::new(Vec3::Y, Vec2::new(20.0, 20.0))),
        material: materials.add(StandardMaterial {
            base_color: Color::srgb(0.65, 0.6, 0.62),
            ..default()
        }),
        transform: Transform::from_xyz(0.0, -0.01, 0.0),
        ..default()
    });
    commands.spawn(PointLightBundle {
        point_light: PointLight {
            intensity: 2_000_000.0,
            range: 30.0,
            shadows_enabled: true,
            ..default()
        },
        transform: Transform::from_xyz(2.0, 4.0, 2.0),
        ..default()
    });
    if let Some(mr) = mesh_res {
        let m = mr.0.to_bevy_mesh();
        info!("spawning character mesh ({} verts)", mr.0.positions.len());
        commands.spawn((
            PbrBundle {
                mesh: meshes.add(m),
                material: materials.add(StandardMaterial {
                    base_color: Color::srgb(0.95, 0.82, 0.78),
                    ..default()
                }),
                transform: Transform::from_scale(Vec3::splat(0.01)),
                ..default()
            },
            CharacterMarker,
        ));
    }
}

fn animate_penis(
    session: Res<gameplay::Session>,
    time: Res<Time>,
    mut q: Query<&mut Transform, With<PenisMarker>>,
) {
    for mut t in &mut q {
        // stroke motion: forward/back along Z with depth
        let stroke = (session.stroke_phase * std::f32::consts::TAU).sin();
        t.translation.z = stroke * session.depth * 0.5;
        t.translation.y = 1.0 + session.depth * 0.3;
    }
}

fn animate_character(
    session: Res<gameplay::Session>,
    time: Res<Time>,
    mut q: Query<&mut Transform, With<CharacterMarker>>,
) {
    for mut t in &mut q {
        let breathe = (time.elapsed_seconds() * 1.5).sin() * 0.004 * (1.0 + session.arousal * 2.0);
        let bob = session.depth * 0.02;
        t.translation.y = breathe + bob;
        t.rotation = Quat::from_rotation_x(session.depth * 0.05);
    }
}

fn spawn_ui(mut commands: Commands) {
    commands.spawn((
        TextBundle::from_section(
            "HyperDeep",
            TextStyle { font_size: 24.0, color: Color::WHITE, ..default() },
        ),
        ui::ArousalMeter,
    ));
}







