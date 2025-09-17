use core_relations::{PlanStrategy, Value};
use numeric_id::NumericId;
use emap::core::NetlistDatabase;
use std::time::Instant;
use std::env;


fn main() {
    let args: Vec<String> = env::args().collect();
    let start = Instant::now();
    let mut netlist = NetlistDatabase::default();
    netlist.build_from_json(&args[1], &args[2], if args.len() > 3 { &args[3] } else { "" });
    netlist.merge_all();
    println!("Build time: {:.2?}", start.elapsed());

    // netlist.print_tables();

    // netlist.rewrite_basic_all(PlanStrategy::PureSize, Value::new(0)..Value::new(1));

    // netlist.merge_all();
    // netlist.print_tables();

    // serde_json::to_writer_pretty(std::fs::File::create("dot_product_out.json").unwrap(), &netlist.dump_tables()).unwrap();
    // netlist.print_tables();

    // let mut db = Database::default();
    // let id_counter = db.add_counter();  // shared by both base and container values
    // let ts_counter = db.add_counter();  // used for timestamps
    // let displaced: core_relations::TableId = db.add_table(DisplacedTable::default(), iter::empty(), iter::empty()); // union-find structure

    // db.base_values_mut().register_type::<i64>();    // register i64
    // db.base_values_mut().register_type::<&'static str>(); // register str
    // db.container_values_mut().register_type::<VecContainer>(id_counter, move |state, old, new| {
    //     if old != new {
    //         let next_ts = Value::from_usize(state.read_counter(ts_counter));
    //         state.stage_insert(displaced, &[old, new, next_ts]);
    //         std::cmp::min(old, new) // TODO: use a better way to determine the "old" value
    //     }
    //     else {
    //         old
    //     }
    // });

    // let wires_impl = SortedWritesTable::new(
    //     1, 3, Some(ColumnId::new(2)), Vec::new(),
    //     Box::new(move |state, expr1, expr2, res| {
    //         if expr1 != expr2 {
    //             state.stage_insert(displaced, &[expr1[1], expr2[1], expr2[2]]);
    //             res.extend_from_slice(expr2);   // expr2 wins
    //             true
    //         }
    //         else {
    //             false
    //         }
    //     })
    // );
    // let wires = db.add_table(wires_impl, iter::once(displaced), iter::once(displaced));

    // // (type, a, b, y, t)
    // let aby_cells_impl = SortedWritesTable::new(
    //     3, 5, Some(ColumnId::new(4)), Vec::new(),
    //     Box::new(move |state, expr1, expr2, res| {
    //         if expr1 != expr2 {
    //             let vec1 = &state.container_values().get_val::<VecContainer>(expr1[3]).unwrap().0;
    //             let vec2 = &state.container_values().get_val::<VecContainer>(expr2[3]).unwrap().0;
    //             assert_eq!(vec1.len(), vec2.len());
    //             for (elem1, elem2) in vec1.iter().zip(vec2.iter()) {    // union each pair of elements
    //                 if elem1 != elem2 { 
    //                     state.stage_insert(displaced, &[*elem1, *elem2, expr2[4]]);
    //                 }
    //             }
    //             // state.stage_insert(displaced, &[expr1[3], expr2[3], expr2[4]]); // union the vecs
    //             res.extend_from_slice(expr2);   // expr2 wins
    //             true
    //         }
    //         else {
    //             false
    //         }
    //     })
    // );
    // let aby_cells = db.add_table(aby_cells_impl, iter::once(displaced), iter::once(displaced));

    // let ts = Value::from_usize(db.inc_counter(ts_counter));
    // // add wires from 0 to 20
    // let mut ws = Vec::new();
    // {
    //     let mut buf = db.get_table(wires).new_buffer();
    //     for i in 0..20 {
    //         let i = db.base_values().get(i as i64);
    //         buf.stage_insert(&[i, Value::from_usize(db.inc_counter(id_counter)), ts]);
    //         ws.push(i);
    //     }
    // }   // flush the buffer
    // db.merge_all();

    // // add types
    // let mut types = HashMap::new();
    // {
    //     types.insert("$add", Value::from_usize(db.inc_counter(id_counter)));
    //     types.insert("$mul", Value::from_usize(db.inc_counter(id_counter)));
    //     types.insert("$sub", Value::from_usize(db.inc_counter(id_counter)));
    // }
    // println!("Types: {:?}", types);

    // // add cells
    // {
    //     let mut buf = db.get_table(aby_cells).new_buffer();
    //     let vec01 = db.with_execution_state(|state| {
    //         state.container_values().register_val(VecContainer(vec![ws[0], ws[1]]), state)
    //     });
    //     let vec23 = db.with_execution_state(|state| {
    //         state.container_values().register_val(VecContainer(vec![ws[2], ws[3]]), state)
    //     });
    //     let vec45 = db.with_execution_state(|state| {
    //         state.container_values().register_val(VecContainer(vec![ws[4], ws[5]]), state)
    //     });
    //     let vec67 = db.with_execution_state(|state| {
    //         state.container_values().register_val(VecContainer(vec![ws[6], ws[7]]), state)
    //     });
    //     let vec89 = db.with_execution_state(|state| {
    //         state.container_values().register_val(VecContainer(vec![ws[8], ws[9]]), state)
    //     });
    //     let vec23_copy = db.with_execution_state(|state| {
    //         state.container_values().register_val(VecContainer(vec![ws[2], ws[3]]), state)
    //     });

    //     println!("{:?}, {:?}, {:?}, {:?}, {:?}, {:?}", vec01, vec23, vec45, vec67, vec89, vec23_copy);

    //     buf.stage_insert(&[types["$add"], vec01, vec23, vec45, ts]);
    //     buf.stage_insert(&[types["$add"], vec23, vec01, vec45, ts]);
    //     buf.stage_insert(&[types["$add"], vec01, vec23, vec67, ts]);
    //     buf.stage_insert(&[types["$mul"], vec01, vec45, vec89, ts]);
    //     buf.stage_insert(&[types["$mul"], vec01, vec67, vec89, ts]);
    // }   // flush the buffer
    // db.merge_all();

    // println!("After merge:");
    // dump_tables(&db, &[displaced, aby_cells]);

    // // rebuild containers
    // loop {
    //     println!("Rebuilding...");
    //     let container_modified = db.rebuild_containers(displaced);
    //     let table_modified = db.apply_rebuild(displaced, &[wires, aby_cells], Value::from_usize(db.inc_counter(ts_counter)));
    //     if !container_modified && !table_modified {
    //         break;  // no more changes
    //     }
    // }

    // println!("After rebuild containers:");
    // dump_tables(&db, &[displaced, aby_cells]);

    // let mut rsb = db.new_rule_set();
    // {
    //     let mut lhs = rsb.new_rule();
    //     let ty = lhs.new_var();
    //     let a = lhs.new_var();
    //     let b = lhs.new_var();
    //     let y = lhs.new_var();
    //     let t = lhs.new_var();
    //     lhs.add_atom(aby_cells, &[ty.into(), a.into(), b.into(), y.into(), t.into()], &[]).unwrap();
    //     let mut rhs = lhs.build();
    //     let id_canons = rhs.lookup_with_default(displaced, &[b.into()], b.into(), ColumnId::new(1)).unwrap();
    //     rhs.assert_ne(b.into(), id_canons.into()).unwrap();
    //     rhs.insert(aby_cells, &[ty.into(), a.into(), id_canons.into(), y.into(), t.into()]).unwrap();
    //     rhs.remove(aby_cells, &[ty.into(), a.into(), b.into()]).unwrap();
    //     rhs.build();
    // }
    // let rs = rsb.build();
    // netlist.db.run_rule_set(&rs);

    // println!("After rebuild tables:");
    // dump_tables(&db, &[displaced, aby_cells]);
}