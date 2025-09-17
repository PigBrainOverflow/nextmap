use core_relations::{
    ColumnId, Constraint, PlanStrategy, Value, WriteVal,
    make_external_func
};
use std::{cell, fmt::Write, ops::Range};
use crate::core::NetlistDatabase;
use numeric_id::NumericId;


impl NetlistDatabase {
    pub fn rewrite_basic_all(&mut self, strategy: PlanStrategy, recent_range: Range<Value>) {
        let old_range = Value::new(0)..recent_range.start;
        let all_range = Value::new(0)..recent_range.end;
        let next_ts = recent_range.end;

        // this is a test
        // let func_id = self.db.add_external_function(make_external_func(move |state, args| -> Option<Value> {
        //     // insert or lookup
        //     println!("External function called: {:?}", args);
        //     None
        // }));

        let mut rsb = self.db.new_rule_set();

        // aby_assoc_to_right
        // (a + b) + c => a + (b + c)
        // let assoc_types = [
        //     "$adds", "$addu", "$muls", "$mulu",
        //     "$and", "$or", "$xor",
        // ];
        // for assoc_type in assoc_types {
        //     for (l_range, r_range) in [ // seminaive evaluation
        //         (all_range.clone(), recent_range.clone()),
        //         (recent_range.clone(), old_range.clone())
        //     ] {
        //         let mut aby_assoc_to_right_lhs = rsb.new_rule();
        //         aby_assoc_to_right_lhs.set_plan_strategy(strategy);
        //         let cell_type = aby_assoc_to_right_lhs.new_var();
        //         let a = aby_assoc_to_right_lhs.new_var();
        //         let b = aby_assoc_to_right_lhs.new_var();
        //         let tmp = aby_assoc_to_right_lhs.new_var();
        //         let c = aby_assoc_to_right_lhs.new_var();
        //         let y = aby_assoc_to_right_lhs.new_var();
        //         let t1 = aby_assoc_to_right_lhs.new_var();
        //         let t2 = aby_assoc_to_right_lhs.new_var();
        //         aby_assoc_to_right_lhs.add_atom(
        //             self.aby_cells,
        //             &[cell_type.into(), a.into(), b.into(), tmp.into(), t1.into()],
        //             &[
        //                 Constraint::GeConst{col: ColumnId::new(4), val: l_range.start},
        //                 Constraint::LtConst{col: ColumnId::new(4), val: l_range.end},   // time range
        //                 Constraint::EqConst{col: ColumnId::new(0), val: *self.types.get_by_left(assoc_type).unwrap()}, // cell type
        //             ]
        //         ).unwrap();
        //         aby_assoc_to_right_lhs.add_atom(
        //             self.aby_cells,
        //             &[cell_type.into(), tmp.into(), c.into(), y.into(), t2.into()],
        //             &[
        //                 Constraint::GeConst{col: ColumnId::new(4), val: r_range.start},
        //                 Constraint::LtConst{col: ColumnId::new(4), val: r_range.end},   // time range
        //                 Constraint::EqConst{col: ColumnId::new(0), val: *self.types.get_by_left(assoc_type).unwrap()}, // cell type
        //             ]
        //         ).unwrap();

        //         let mut aby_assoc_to_right_rhs = aby_assoc_to_right_lhs.build();
        //         aby_assoc_to_right_rhs.lookup_or_insert(
        //                 self.aby_cells
        //                 &[cell_type.into(), b.into(), c.into(), 
        //                 &[
        //                     WriteVal::IncCounter(id_counter),
        //                     WriteVal::QueryEntry(next_ts.into()),
        //                 ],
        //                 ColumnId::new(2),
        //             )
        //             .unwrap();
        //         rules
        //             .insert(add, &[res.into(), z.into(), i2.into(), next_ts.into()])
        //             .unwrap();
        //         rules.build();
        //     }
        // }

        // aby_comm
        // a + b => b + a
        let comm_types = [
            "$adds", "$addu", "$muls", "$mulu",
            "$and", "$or", "$xor",
        ];
        for comm_type in comm_types {
            let mut aby_comm_lhs = rsb.new_rule();
            aby_comm_lhs.set_plan_strategy(strategy);
            let cell_type = aby_comm_lhs.new_var();
            let a = aby_comm_lhs.new_var();
            let b = aby_comm_lhs.new_var();
            let y = aby_comm_lhs.new_var();
            let t = aby_comm_lhs.new_var();
            aby_comm_lhs.add_atom(
                self.aby_cells,
                &[cell_type.into(), a.into(), b.into(), y.into(), t.into()],
                &[
                    Constraint::EqConst{col: ColumnId::new(4), val: recent_range.start},    // current timestamp
                    Constraint::EqConst{col: ColumnId::new(0), val: *self.types.get_by_left(comm_type).unwrap()}, // cell type
                ]
            ).unwrap();

            let mut aby_comm_rhs = aby_comm_lhs.build();
            aby_comm_rhs.insert(
                self.aby_cells,
                &[cell_type.into(), b.into(), a.into(), y.into(), next_ts.into()]
            ).unwrap();
            aby_comm_rhs.build();
        }

        // finish and run the rule set
        let rs = rsb.build();
        self.db.run_rule_set(&rs);
    }
}