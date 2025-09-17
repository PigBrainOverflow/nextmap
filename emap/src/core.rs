use core_relations::{CounterId, Database, DisplacedTable, TableId, Value, Rebuilder, ContainerValue, SortedWritesTable, ColumnId};
use numeric_id::NumericId;
use serde_json::json;
use core::panic;
use std::{
    time::Instant,
    collections::HashMap,
    fmt::Debug,
    iter
};
use bimap::BiHashMap;


pub struct NetlistDatabase {
    pub(crate) db: Database,
    pub(crate) id_counter: CounterId,
    pub(crate) ts_counter: CounterId,
    pub(crate) displaced: TableId,
    pub(crate) ay_cells: TableId,
    pub(crate) aby_cells: TableId,
    pub(crate) absy_cells: TableId,
    pub(crate) dffs: TableId,
    pub(crate) types: BiHashMap<String, Value>,  // we use external containers to record types and wires
    pub(crate) wires: BiHashMap<i64, Value>,
    pub(crate) clk: i64,
    pub(crate) from_inputs: HashMap<(String, i64), i64>,   // (port name, index) -> wire id
    pub(crate) as_outputs: HashMap<(String, i64), i64>
}

#[derive(Clone, Debug, Hash, Eq, PartialEq)]
struct VecContainer(Vec<Value>);
impl ContainerValue for VecContainer {
    fn rebuild_contents(&mut self, rebuilder: &dyn Rebuilder) -> bool {
        rebuilder.rebuild_slice(&mut self.0)
    }

    fn iter(&self) -> impl Iterator<Item = Value> + '_ {
        self.0.iter().copied()
    }
}

impl NetlistDatabase {
    pub(crate) const AY_TYPES: &[&str] = &["$not", "$logic_not"];
    pub(crate) const ABY_TYPES: &[&str] = &[
        "$and", "$or", "$xor", "$nand", "$nor", "$xnor",
        "$eq", "$ge", "$le", "$gt", "$lt", "$logic_and", "$logic_or",
        "$adds", "$addu", "$subs", "$subu", "$muls", "$mulu", "$divs", "$divu", "$mod"
    ];
    pub(crate) const ABSY_TYPES: &[&str] = &["$mux"];

    pub(crate) const RTLIL_AY_TYPES: &[&str] = &["$not", "$logic_not"];
    pub(crate) const RTLIL_ABY_ARITH_TYPES: &[&str] = &["$add", "$sub", "$mul", "$div", "$mod"];
    pub(crate) const RTLIL_ABY_LOGIC_TYPES: &[&str] = &[
        "$and", "$or", "$xor", "$nand", "$nor", "$xnor",
        "$eq", "$ge", "$le", "$gt", "$lt", "$logic_and", "$logic_or"
    ];
    pub(crate) const RTLIL_ABSY_TYPES: &[&str] = &["$mux"];

    // auxiliary functions
    fn bit_to_i64(bit: &serde_json::Value) -> i64 {
        match bit {
            serde_json::Value::Number(num) => num.as_i64().unwrap(),
            serde_json::Value::String(s) => {
                match s.as_str() {
                    "x" => -1,
                    "0" => 0,
                    "1" => 1,
                    _ => panic!("Invalid bit value: {}", s),
                }
            }
            _ => panic!("Invalid bit value: {:?}", bit),
        }
    }

    fn param_to_i64(param: &serde_json::Value) -> i64 {
        match param {
            serde_json::Value::Number(num) => num.as_i64().unwrap(),
            serde_json::Value::String(s) => i64::from_str_radix(s, 2).unwrap(),
            _ => panic!("Invalid parameter value: {:?}", param),
        }
    }

    fn create_wire(&mut self, wire: i64) -> Value {
        let new_val = Value::from_usize(self.db.inc_counter(self.id_counter));
        self.wires.insert(wire, new_val);
        new_val
    }

    fn create_or_lookup_wire(&mut self, wire: i64) -> Value {
        if let Some(val) = self.wires.get_by_left(&wire) {
            return *val;
        }
        self.create_wire(wire)
    }

    fn create_or_lookup_wirevec_from_json(&mut self, bits: &serde_json::Value) -> Value {
        let vec: Vec<Value> = bits.as_array().unwrap()
            .iter()
            .map(|b| self.create_or_lookup_wire(Self::bit_to_i64(b)))
            .collect();
        self.db.with_execution_state(|state| {
            state.container_values().register_val(VecContainer(vec), state)
        })
    }

    pub fn print_tables(&self) {
        self.db.container_values().for_each::<VecContainer>(|vec, expr| {
            println!("Container {:?}: {:?}", expr, vec);
        });

        for table_id in &[self.ay_cells, self.aby_cells, self.absy_cells, self.dffs] {
            let table = self.db.get_table(*table_id);
            let rows = table.all();
            let rows = table.scan(rows.as_ref());
            for row in rows.iter() {
                println!("Table {:?}: {:?}", table_id, row);
            }
        }
    }

    pub fn dump_tables(&self) -> serde_json::Value {
        let mut wirevecs = Vec::new();
        self.db.container_values().for_each::<VecContainer>(|vec, expr| {
            wirevecs.push(json!({
                "id": expr.rep(),
                "wires": vec.0.iter().map(|v| v.rep()).collect::<Vec<_>>()
            }));
        });
        json!({
            "wirevecs": wirevecs
        })
    }

    pub fn merge_all(&mut self) {
        self.db.merge_all();
    }

    pub fn default() -> Self {
        let mut db = Database::default();
        let id_counter = db.add_counter();  // shared by both base and container values
        let ts_counter = db.add_counter();  // used for timestamps
        let displaced = db.add_table(DisplacedTable::default(), iter::empty(), iter::empty()); // union-find structure

        db.base_values_mut().register_type::<i64>();    // register i64
        db.base_values_mut().register_type::<&'static str>(); // register str
        db.container_values_mut().register_type::<VecContainer>(id_counter, move |state, old, new| {
            if old != new {
                let next_ts = Value::from_usize(state.read_counter(ts_counter));
                state.stage_insert(displaced, &[old, new, next_ts]);
                std::cmp::min(old, new)
            }
            else {
                old
            }
        });

        // (type, a, y, t)
        let ay_cells_impl = SortedWritesTable::new(
            2, 4, Some(ColumnId::new(3)), Vec::new(),
            Box::new(move |state, expr1, expr2, res| {
                if expr1 != expr2 {
                    let vec1 = &state.container_values().get_val::<VecContainer>(expr1[2]).unwrap().0;
                    let vec2 = &state.container_values().get_val::<VecContainer>(expr2[2]).unwrap().0;
                    assert_eq!(vec1.len(), vec2.len());
                    for (elem1, elem2) in vec1.iter().zip(vec2.iter()) {    // union each pair of elements
                        if elem1 != elem2 {
                            state.stage_insert(displaced, &[*elem1, *elem2, expr2[3]]);
                        }
                    }
                    res.extend_from_slice(expr2);   // expr2 wins
                    true
                }
                else {
                    false
                }
            })
        );
        let ay_cells = db.add_table(ay_cells_impl, iter::once(displaced), iter::once(displaced));

        // (type, a, b, y, t)
        let aby_cells_impl = SortedWritesTable::new(
            3, 5, Some(ColumnId::new(4)), Vec::new(),
            Box::new(move |state, expr1, expr2, res| {
                if expr1 != expr2 {
                    let vec1 = &state.container_values().get_val::<VecContainer>(expr1[3]).unwrap().0;
                    let vec2 = &state.container_values().get_val::<VecContainer>(expr2[3]).unwrap().0;
                    assert_eq!(vec1.len(), vec2.len());
                    for (elem1, elem2) in vec1.iter().zip(vec2.iter()) {    // union each pair of elements
                        if elem1 != elem2 {
                            state.stage_insert(displaced, &[*elem1, *elem2, expr2[4]]);
                        }
                    }
                    // state.stage_insert(displaced, &[expr1[3], expr2[3], expr2[4]]); // union the vecs
                    res.extend_from_slice(expr2);   // expr2 wins
                    true
                }
                else {
                    false
                }
            })
        );
        let aby_cells = db.add_table(aby_cells_impl, iter::once(displaced), iter::once(displaced));

        let absy_cells_impl = SortedWritesTable::new(
            4, 6, Some(ColumnId::new(5)), Vec::new(),
            Box::new(move |state, expr1, expr2, res| {
                if expr1 != expr2 {
                    let vec1 = &state.container_values().get_val::<VecContainer>(expr1[4]).unwrap().0;
                    let vec2 = &state.container_values().get_val::<VecContainer>(expr2[4]).unwrap().0;
                    assert_eq!(vec1.len(), vec2.len());
                    for (elem1, elem2) in vec1.iter().zip(vec2.iter()) {    // union each pair of elements
                        if elem1 != elem2 {
                            state.stage_insert(displaced, &[*elem1, *elem2, expr2[5]]);
                        }
                    }
                    res.extend_from_slice(expr2);   // expr2 wins
                    true
                }
                else {
                    false
                }
            })
        );
        let absy_cells = db.add_table(absy_cells_impl, iter::once(displaced), iter::once(displaced));

        let dffs_impl = SortedWritesTable::new(
            1, 3, Some(ColumnId::new(2)), Vec::new(),
            Box::new(move |state, expr1, expr2, res| {
                if expr1 != expr2 {
                    let vec1 = &state.container_values().get_val::<VecContainer>(expr1[1]).unwrap().0;
                    let vec2 = &state.container_values().get_val::<VecContainer>(expr2[1]).unwrap().0;
                    assert_eq!(vec1.len(), vec2.len());
                    for (elem1, elem2) in vec1.iter().zip(vec2.iter()) {    // union each pair of elements
                        if elem1 != elem2 {
                            state.stage_insert(displaced, &[*elem1, *elem2, expr2[2]]);
                        }
                    }
                    res.extend_from_slice(expr2);   // expr2 wins
                    true
                }
                else {
                    false
                }
            })
        );
        let dffs = db.add_table(dffs_impl, iter::once(displaced), iter::once(displaced));

        let mut types = BiHashMap::new();
        for ty in Self::AY_TYPES.iter().chain(Self::ABY_TYPES.iter()).chain(Self::ABSY_TYPES.iter()) {
            types.insert(ty.to_string(), Value::from_usize(db.inc_counter(id_counter)));
        }

        Self{
            db, id_counter, ts_counter,
            displaced, ay_cells, aby_cells, absy_cells, dffs,
            types, wires: BiHashMap::new(), clk: -1, from_inputs: HashMap::new(), as_outputs: HashMap::new()
        }
    }

    pub fn build_from_json(&mut self, json_path: &str, top_mod: &str, clk_name: &str) {
        let data = std::fs::read_to_string(json_path)
            .expect("Failed to read JSON file");
        let netlist: serde_json::Value = serde_json::from_str(&data).unwrap();
        println!("Successfully loaded JSON netlist from {}", json_path);
        let top_module = netlist.get("modules")
            .and_then(|m| m.get(top_mod))
            .expect("Top module not found");
        self.build_mod(top_module, clk_name);
    }

    fn build_ay_cell<'a>(&mut self, cell: &'a serde_json::Value, ts: Value) -> Option<&'a serde_json::Value> {
        // return None if the cell is processed
        let cell_type = cell.get("type").and_then(|d| d.as_str()).unwrap();
        if !Self::RTLIL_AY_TYPES.contains(&cell_type) {
            Some(cell)
        }
        else {
            let conns = cell.get("connections").and_then(|d| d.as_object()).unwrap();
            self.db
                .get_table(self.ay_cells)
                .new_buffer().stage_insert(&[
                    *self.types.get_by_left(cell_type).unwrap(),
                    self.create_or_lookup_wirevec_from_json(conns.get("A").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("Y").unwrap()),
                    ts
                ]);
            None
        }
    }

    fn build_aby_arith_cell<'a>(&mut self, cell: &'a serde_json::Value, ts: Value) -> Option<&'a serde_json::Value> {
        // return None if the cell is processed
        let cell_type = cell.get("type").and_then(|d| d.as_str()).unwrap();
        if !Self::RTLIL_ABY_ARITH_TYPES.contains(&cell_type) {
            Some(cell)
        }
        else {
            let params = cell.get("parameters").and_then(|d| d.as_object()).unwrap();
            let conns = cell.get("connections").and_then(|d| d.as_object()).unwrap();
            let a_signed = params.get("A_SIGNED")
                .map(|d| Self::param_to_i64(d) != 0)
                .unwrap_or(false);
            let b_signed = params.get("B_SIGNED")
                .map(|d| Self::param_to_i64(d) != 0)
                .unwrap_or(false);
            let cell_type = match a_signed && b_signed {
                true => [cell_type, "s"].concat(),
                false => [cell_type, "u"].concat()
            };

            self.db
                .get_table(self.aby_cells)
                .new_buffer().stage_insert(&[
                    *self.types.get_by_left(&cell_type).unwrap(),
                    self.create_or_lookup_wirevec_from_json(conns.get("A").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("B").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("Y").unwrap()),
                    ts
                ]);
            None
        }
    }

    fn build_aby_logic_cell<'a>(&mut self, cell: &'a serde_json::Value, ts: Value) -> Option<&'a serde_json::Value> {
        // return None if the cell is processed
        let cell_type = cell.get("type").and_then(|d| d.as_str()).unwrap();
        if !Self::RTLIL_ABY_LOGIC_TYPES.contains(&cell_type) {
            Some(cell)
        }
        else {
            let conns = cell.get("connections").and_then(|d| d.as_object()).unwrap();
            self.db
                .get_table(self.aby_cells)
                .new_buffer().stage_insert(&[
                    *self.types.get_by_left(cell_type).unwrap(),
                    self.create_or_lookup_wirevec_from_json(conns.get("A").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("B").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("Y").unwrap()),
                    ts
                ]);
            None
        }
    }

    fn build_absy_cell<'a>(&mut self, cell: &'a serde_json::Value, ts: Value) -> Option<&'a serde_json::Value> {
        // return None if the cell is processed
        let cell_type = cell.get("type").and_then(|d| d.as_str()).unwrap();
        if !Self::RTLIL_ABSY_TYPES.contains(&cell_type) {
            Some(cell)
        }
        else {
            let conns = cell.get("connections").and_then(|d| d.as_object()).unwrap();
            self.db
                .get_table(self.absy_cells)
                .new_buffer().stage_insert(&[
                    *self.types.get_by_left(cell_type).unwrap(),
                    self.create_or_lookup_wirevec_from_json(conns.get("A").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("B").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("S").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("Y").unwrap()),
                    ts
                ]);
            None
        }
    }

    fn build_dff_cell<'a>(&mut self, cell: &'a serde_json::Value, ts: Value) -> Option<&'a serde_json::Value> {
        // return None if the cell is processed
        let cell_type = cell.get("type").and_then(|d| d.as_str()).unwrap();
        if cell_type != "$dff" {
            Some(cell)
        }
        else {
            let conns = cell.get("connections").and_then(|d| d.as_object()).unwrap();
            let clk = conns.get("CLK").and_then(|d| d.as_array()).and_then(|a| a.iter().map(Self::bit_to_i64).collect::<Vec<_>>().into()).unwrap();
            if clk.len() != 1 || clk[0] != self.clk {
                panic!("DFF cell clock must be the same as the global clock");
            }
            self.db
                .get_table(self.dffs)
                .new_buffer().stage_insert(&[
                    self.create_or_lookup_wirevec_from_json(conns.get("D").unwrap()),
                    self.create_or_lookup_wirevec_from_json(conns.get("Q").unwrap()),
                    ts
                ]);
            None
        }
    }

    pub fn build_mod(&mut self, top_mod: &serde_json::Value, clk_name: &str) {
        let start = Instant::now();

        // build inputs & outputs
        let ports = top_mod.get("ports").and_then(|d| d.as_object()).unwrap();
        for (name, port) in ports.iter() {
            let direction = port
                .get("direction")
                .and_then(|d| d.as_str())
                .unwrap();
            let bits = port
                .get("bits")
                .and_then(|d| d.as_array())
                .and_then(|a| a.iter()
                    .map(Self::bit_to_i64)
                    .collect::<Vec<_>>()
                    .into()
                )
                .unwrap();
            match direction {
                "input" => {
                    if name == clk_name {
                        if bits.len() != 1 {
                            panic!("Clock port must have exactly one bit");
                        }
                        self.clk = bits[0];
                    }
                    for (i, bit) in bits.iter().enumerate() {
                        self.from_inputs.insert((name.clone(), i as i64), *bit);
                        self.create_wire(*bit);
                    }
                },
                "output" => {
                    for (i, bit) in bits.iter().enumerate() {
                        self.as_outputs.insert((name.clone(), i as i64), *bit);
                        self.create_wire(*bit);
                    }
                },
                _ => panic!("Unknown port direction: {}", direction)
            }
        }

        // build cells
        let cells = top_mod.get("cells").and_then(|d| d.as_object()).unwrap();
        println!("Found {} cells to process", cells.len());
        for (i, (name, cell)) in cells.iter().enumerate() {
            if i % 1000 == 0 {
                println!("Processing cell {}/{}: {}", i, cells.len(), name);
            }

            // chain of cell processing functions
            let res = self.build_ay_cell(cell, Value::new(0))
                .and_then(|c| self.build_aby_arith_cell(c, Value::new(0)))
                .and_then(|c| self.build_aby_logic_cell(c, Value::new(0)))
                .and_then(|c| self.build_absy_cell(c, Value::new(0)))
                .and_then(|c| self.build_dff_cell(c, Value::new(0)));
            if let Some(_) = res {
                println!("Unprocessed cell: {}", name);
            }
        }
    }
}