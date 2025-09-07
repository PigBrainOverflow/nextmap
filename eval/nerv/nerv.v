module nerv (
	clock,
	reset,
	stall,
	trap,
	imem_addr,
	imem_data,
	dmem_valid,
	dmem_addr,
	dmem_wstrb,
	dmem_wdata,
	dmem_rdata,
	irq
);
	parameter [31:0] RESET_ADDR = 32'h00000000;
	parameter integer NUMREGS = 32;
	input clock;
	input reset;
	input stall;
	output wire trap;
	output wire [31:0] imem_addr;
	input [31:0] imem_data;
	output wire dmem_valid;
	output wire [31:0] dmem_addr;
	output wire [3:0] dmem_wstrb;
	output wire [31:0] dmem_wdata;
	input [31:0] dmem_rdata;
	input [31:0] irq;
	wire imem_fault = 0;
	wire dmem_fault = 0;
	reg mem_wr_enable;
	reg [31:0] mem_wr_addr;
	reg [31:0] mem_wr_data;
	reg [3:0] mem_wr_strb;
	reg mem_rd_enable;
	reg [31:0] mem_rd_addr;
	reg [4:0] mem_rd_reg;
	reg [4:0] mem_rd_func;
	reg [31:0] mem_rdata;
	reg mem_rd_enable_q;
	reg [4:0] mem_rd_reg_q;
	reg [4:0] mem_rd_func_q;
	reg mem_wr_enable_q;
	always @(posedge clock) begin
		if (!stall) begin
			mem_rd_enable_q <= mem_rd_enable;
			mem_rd_reg_q <= mem_rd_reg;
			mem_rd_func_q <= mem_rd_func;
			mem_wr_enable_q <= mem_wr_enable;
		end
		if (reset)
			mem_rd_enable_q <= 0;
	end
	assign dmem_valid = mem_wr_enable || mem_rd_enable;
	assign dmem_addr = (mem_wr_enable ? mem_wr_addr : (mem_rd_enable ? mem_rd_addr : 32'hxxxxxxxx));
	assign dmem_wstrb = (mem_wr_enable ? mem_wr_strb : (mem_rd_enable ? 4'h0 : 4'hx));
	assign dmem_wdata = (mem_wr_enable ? mem_wr_data : 32'hxxxxxxxx);
	reg [31:0] regfile [0:NUMREGS - 1];
	wire [31:0] insn;
	reg [31:0] npc;
	reg [31:0] pc;
	reg [31:0] imem_addr_q;
	always @(posedge clock) imem_addr_q <= imem_addr;
	assign imem_addr = npc;
	assign insn = imem_data;
	wire [6:0] insn_funct7;
	wire [4:0] insn_rs2;
	wire [4:0] insn_rs1;
	wire [2:0] insn_funct3;
	wire [4:0] insn_rd;
	wire [6:0] insn_opcode;
	wire [31:0] rs1_value = (!insn_rs1 ? 0 : regfile[insn_rs1]);
	wire [31:0] rs2_value = (!insn_rs2 ? 0 : regfile[insn_rs2]);
	assign {insn_funct7, insn_rs2, insn_rs1, insn_funct3, insn_rd, insn_opcode} = insn;
	wire [11:0] imm_i;
	assign imm_i = insn[31:20];
	wire [11:0] imm_s;
	assign imm_s[11:5] = insn_funct7;
	assign imm_s[4:0] = insn_rd;
	wire [12:0] imm_b;
	assign {imm_b[12], imm_b[10:5]} = insn_funct7;
	assign {imm_b[4:1], imm_b[11]} = insn_rd;
	assign imm_b[0] = 1'b0;
	wire [20:0] imm_j;
	assign {imm_j[20], imm_j[10:1], imm_j[11], imm_j[19:12], imm_j[0]} = {insn[31:12], 1'b0};
	wire [31:0] imm_i_sext = $signed(imm_i);
	wire [31:0] imm_s_sext = $signed(imm_s);
	wire [31:0] imm_b_sext = $signed(imm_b);
	wire [31:0] imm_j_sext = $signed(imm_j);
	localparam OPCODE_LOAD = 7'b0000011;
	localparam OPCODE_STORE = 7'b0100011;
	localparam OPCODE_MADD = 7'b1000011;
	localparam OPCODE_BRANCH = 7'b1100011;
	localparam OPCODE_LOAD_FP = 7'b0000111;
	localparam OPCODE_STORE_FP = 7'b0100111;
	localparam OPCODE_MSUB = 7'b1000111;
	localparam OPCODE_JALR = 7'b1100111;
	localparam OPCODE_CUSTOM_0 = 7'b0001011;
	localparam OPCODE_CUSTOM_1 = 7'b0101011;
	localparam OPCODE_NMSUB = 7'b1001011;
	localparam OPCODE_RESERVED_0 = 7'b1101011;
	localparam OPCODE_MISC_MEM = 7'b0001111;
	localparam OPCODE_AMO = 7'b0101111;
	localparam OPCODE_NMADD = 7'b1001111;
	localparam OPCODE_JAL = 7'b1101111;
	localparam OPCODE_OP_IMM = 7'b0010011;
	localparam OPCODE_OP = 7'b0110011;
	localparam OPCODE_OP_FP = 7'b1010011;
	localparam OPCODE_SYSTEM = 7'b1110011;
	localparam OPCODE_AUIPC = 7'b0010111;
	localparam OPCODE_LUI = 7'b0110111;
	localparam OPCODE_RESERVED_1 = 7'b1010111;
	localparam OPCODE_RESERVED_2 = 7'b1110111;
	localparam OPCODE_OP_IMM_32 = 7'b0011011;
	localparam OPCODE_OP_32 = 7'b0111011;
	localparam OPCODE_CUSTOM_2 = 7'b1011011;
	localparam OPCODE_CUSTOM_3 = 7'b1111011;
	localparam MCAUSE_MACHINE_SOFTWARE_INTERRUPT = 32'h80000003;
	localparam MCAUSE_MACHINE_TIMER_INTERRUPT = 32'h80000007;
	localparam MCAUSE_MACHINE_EXTERNAL_INTERRUPT = 32'h8000000b;
	localparam MCAUSE_INSN_ADDRESS_MISALIGNED = 32'h00000000;
	localparam MCAUSE_INSN_ACCESS_FAULT = 32'h00000001;
	localparam MCAUSE_INVALID_INSTRUCTION = 32'h00000002;
	localparam MCAUSE_BREAKPOINT = 32'h00000003;
	localparam MCAUSE_LOAD_ADDRESS_MISALIGNED = 32'h00000004;
	localparam MCAUSE_LOAD_ACCESS_FAULT = 32'h00000005;
	localparam MCAUSE_STORE_ADDRESS_MISALIGNED = 32'h00000006;
	localparam MCAUSE_STORE_ACCESS_FAULT = 32'h00000007;
	localparam MCAUSE_ECALL_M_MODE = 32'h0000000b;
	localparam IRQ_MASK = 32'hffff0888;
	reg [4:0] irq_num;
	reg next_wr;
	reg [31:0] next_rd;
	reg [4:0] wr_rd;
	reg illinsn;
	reg reset_q;
	wire running = (!stall && !reset) && !reset_q;
	reg cycle_intr;
	reg cycle_insn;
	reg cycle_trap;
	reg cycle_late_wr;
	assign trap = cycle_trap;
	reg csr_ack;
	reg [31:0] csr_rdval;
	reg [31:0] csr_next;
	wire imem_valid = (!mem_rd_enable_q && !mem_wr_enable_q) && !imem_fault;
	wire [1:0] csr_mode = (((running && imem_valid) && !irq_num) && (insn_opcode == OPCODE_SYSTEM) ? insn_funct3[1:0] : 2'b00);
	wire [11:0] csr_addr = imm_i;
	wire [31:0] csr_rsval = (insn_funct3[2] ? insn_rs1 : rs1_value);
	wire csr_ro = csr_mode && ((csr_mode != 2'b01) && !insn_rs1);
	integer hpm_idx;
	integer hpm_increment;
	integer hpm_event;
	wire csr_mvendorid_sel = csr_ro && (csr_addr == 12'hf11);
	localparam [31:0] csr_mvendorid_value = 32'h00000000;
	wire csr_marchid_sel = csr_ro && (csr_addr == 12'hf12);
	localparam [31:0] csr_marchid_value = 32'h00000000;
	wire csr_mimpid_sel = csr_ro && (csr_addr == 12'hf13);
	localparam [31:0] csr_mimpid_value = 32'h00000000;
	wire csr_mhartid_sel = csr_ro && (csr_addr == 12'hf14);
	localparam [31:0] csr_mhartid_value = 32'h00000000;
	wire csr_mconfigptr_sel = csr_ro && (csr_addr == 12'hf15);
	localparam [31:0] csr_mconfigptr_value = 32'h00000000;
	wire csr_mstatus_sel = csr_mode && (csr_addr == 12'h300);
	reg [31:0] csr_mstatus_value;
	reg [31:0] csr_mstatus_wdata;
	reg [31:0] csr_mstatus_next;
	always @(posedge clock) begin
		csr_mstatus_value <= csr_mstatus_next;
		if (reset || reset_q)
			csr_mstatus_value <= 32'h00000000;
	end
	wire csr_misa_sel = csr_mode && (csr_addr == 12'h301);
	reg [31:0] csr_misa_value;
	reg [31:0] csr_misa_wdata;
	reg [31:0] csr_misa_next;
	always @(posedge clock) begin
		csr_misa_value <= csr_misa_next;
		if (reset || reset_q)
			csr_misa_value <= 32'h00000000;
	end
	wire csr_mie_sel = csr_mode && (csr_addr == 12'h304);
	reg [31:0] csr_mie_value;
	reg [31:0] csr_mie_wdata;
	reg [31:0] csr_mie_next;
	always @(posedge clock) begin
		csr_mie_value <= csr_mie_next;
		if (reset || reset_q)
			csr_mie_value <= 32'h00000000;
	end
	wire csr_mtvec_sel = csr_mode && (csr_addr == 12'h305);
	reg [31:0] csr_mtvec_value;
	reg [31:0] csr_mtvec_wdata;
	reg [31:0] csr_mtvec_next;
	always @(posedge clock) begin
		csr_mtvec_value <= csr_mtvec_next;
		if (reset || reset_q)
			csr_mtvec_value <= 32'h00000000;
	end
	wire csr_mstatush_sel = csr_mode && (csr_addr == 12'h310);
	reg [31:0] csr_mstatush_value;
	reg [31:0] csr_mstatush_wdata;
	reg [31:0] csr_mstatush_next;
	always @(posedge clock) begin
		csr_mstatush_value <= csr_mstatush_next;
		if (reset || reset_q)
			csr_mstatush_value <= 32'h00000000;
	end
	wire csr_mscratch_sel = csr_mode && (csr_addr == 12'h340);
	reg [31:0] csr_mscratch_value;
	reg [31:0] csr_mscratch_wdata;
	reg [31:0] csr_mscratch_next;
	always @(posedge clock) begin
		csr_mscratch_value <= csr_mscratch_next;
		if (reset || reset_q)
			csr_mscratch_value <= 32'h00000000;
	end
	wire csr_mepc_sel = csr_mode && (csr_addr == 12'h341);
	reg [31:0] csr_mepc_value;
	reg [31:0] csr_mepc_wdata;
	reg [31:0] csr_mepc_next;
	always @(posedge clock) begin
		csr_mepc_value <= csr_mepc_next;
		if (reset || reset_q)
			csr_mepc_value <= 32'h00000000;
	end
	wire csr_mcause_sel = csr_mode && (csr_addr == 12'h342);
	reg [31:0] csr_mcause_value;
	reg [31:0] csr_mcause_wdata;
	reg [31:0] csr_mcause_next;
	always @(posedge clock) begin
		csr_mcause_value <= csr_mcause_next;
		if (reset || reset_q)
			csr_mcause_value <= 32'h00000000;
	end
	wire csr_mtval_sel = csr_mode && (csr_addr == 12'h343);
	reg [31:0] csr_mtval_value;
	reg [31:0] csr_mtval_wdata;
	reg [31:0] csr_mtval_next;
	always @(posedge clock) begin
		csr_mtval_value <= csr_mtval_next;
		if (reset || reset_q)
			csr_mtval_value <= 32'h00000000;
	end
	wire csr_mip_sel = csr_mode && (csr_addr == 12'h344);
	reg [31:0] csr_mip_value;
	reg [31:0] csr_mip_wdata;
	reg [31:0] csr_mip_next;
	always @(posedge clock) begin
		csr_mip_value <= csr_mip_next;
		if (reset || reset_q)
			csr_mip_value <= 32'h00000000;
	end
	integer hpm_counter_idx;
	wire [31:0] csr_hpm_counter_sel;
	reg [1023:0] csr_hpm_counter_value;
	reg [1023:0] csr_hpm_counter_wdata;
	reg [1023:0] csr_hpm_counter_next;
	always @(posedge clock) begin
		csr_hpm_counter_value <= csr_hpm_counter_next;
		if (reset || reset_q)
			csr_hpm_counter_value <= 'b0;
	end
	wire csr_mcycle_sel = csr_mode && (csr_addr == 12'hb00);
	wire [31:0] csr_mcycle_value = csr_hpm_counter_value[0+:32];
	wire [31:0] csr_mcycle_wdata = csr_hpm_counter_wdata[0+:32];
	wire [31:0] csr_mcycle_next = csr_hpm_counter_next[0+:32];
	assign csr_hpm_counter_sel[0] = csr_mcycle_sel;
	wire csr_minstret_sel = csr_mode && (csr_addr == 12'hb02);
	wire [31:0] csr_minstret_value = csr_hpm_counter_value[64+:32];
	wire [31:0] csr_minstret_wdata = csr_hpm_counter_wdata[64+:32];
	wire [31:0] csr_minstret_next = csr_hpm_counter_next[64+:32];
	assign csr_hpm_counter_sel[2] = csr_minstret_sel;
	wire csr_mhpmcounter3_sel = csr_mode && (csr_addr == 12'hb03);
	wire [31:0] csr_mhpmcounter3_value = csr_hpm_counter_value[96+:32];
	wire [31:0] csr_mhpmcounter3_wdata = csr_hpm_counter_wdata[96+:32];
	wire [31:0] csr_mhpmcounter3_next = csr_hpm_counter_next[96+:32];
	assign csr_hpm_counter_sel[3] = csr_mhpmcounter3_sel;
	wire csr_mhpmcounter4_sel = csr_mode && (csr_addr == 12'hb04);
	wire [31:0] csr_mhpmcounter4_value = csr_hpm_counter_value[128+:32];
	wire [31:0] csr_mhpmcounter4_wdata = csr_hpm_counter_wdata[128+:32];
	wire [31:0] csr_mhpmcounter4_next = csr_hpm_counter_next[128+:32];
	assign csr_hpm_counter_sel[4] = csr_mhpmcounter4_sel;
	wire csr_mhpmcounter5_sel = csr_mode && (csr_addr == 12'hb05);
	wire [31:0] csr_mhpmcounter5_value = csr_hpm_counter_value[160+:32];
	wire [31:0] csr_mhpmcounter5_wdata = csr_hpm_counter_wdata[160+:32];
	wire [31:0] csr_mhpmcounter5_next = csr_hpm_counter_next[160+:32];
	assign csr_hpm_counter_sel[5] = csr_mhpmcounter5_sel;
	wire csr_mhpmcounter6_sel = csr_mode && (csr_addr == 12'hb06);
	wire [31:0] csr_mhpmcounter6_value = csr_hpm_counter_value[192+:32];
	wire [31:0] csr_mhpmcounter6_wdata = csr_hpm_counter_wdata[192+:32];
	wire [31:0] csr_mhpmcounter6_next = csr_hpm_counter_next[192+:32];
	assign csr_hpm_counter_sel[6] = csr_mhpmcounter6_sel;
	wire csr_mhpmcounter7_sel = csr_mode && (csr_addr == 12'hb07);
	wire [31:0] csr_mhpmcounter7_value = csr_hpm_counter_value[224+:32];
	wire [31:0] csr_mhpmcounter7_wdata = csr_hpm_counter_wdata[224+:32];
	wire [31:0] csr_mhpmcounter7_next = csr_hpm_counter_next[224+:32];
	assign csr_hpm_counter_sel[7] = csr_mhpmcounter7_sel;
	wire csr_mhpmcounter8_sel = csr_mode && (csr_addr == 12'hb08);
	wire [31:0] csr_mhpmcounter8_value = csr_hpm_counter_value[256+:32];
	wire [31:0] csr_mhpmcounter8_wdata = csr_hpm_counter_wdata[256+:32];
	wire [31:0] csr_mhpmcounter8_next = csr_hpm_counter_next[256+:32];
	assign csr_hpm_counter_sel[8] = csr_mhpmcounter8_sel;
	wire csr_mhpmcounter9_sel = csr_mode && (csr_addr == 12'hb09);
	wire [31:0] csr_mhpmcounter9_value = csr_hpm_counter_value[288+:32];
	wire [31:0] csr_mhpmcounter9_wdata = csr_hpm_counter_wdata[288+:32];
	wire [31:0] csr_mhpmcounter9_next = csr_hpm_counter_next[288+:32];
	assign csr_hpm_counter_sel[9] = csr_mhpmcounter9_sel;
	wire csr_mhpmcounter10_sel = csr_mode && (csr_addr == 12'hb0a);
	wire [31:0] csr_mhpmcounter10_value = csr_hpm_counter_value[320+:32];
	wire [31:0] csr_mhpmcounter10_wdata = csr_hpm_counter_wdata[320+:32];
	wire [31:0] csr_mhpmcounter10_next = csr_hpm_counter_next[320+:32];
	assign csr_hpm_counter_sel[10] = csr_mhpmcounter10_sel;
	wire csr_mhpmcounter11_sel = csr_mode && (csr_addr == 12'hb0b);
	wire [31:0] csr_mhpmcounter11_value = csr_hpm_counter_value[352+:32];
	wire [31:0] csr_mhpmcounter11_wdata = csr_hpm_counter_wdata[352+:32];
	wire [31:0] csr_mhpmcounter11_next = csr_hpm_counter_next[352+:32];
	assign csr_hpm_counter_sel[11] = csr_mhpmcounter11_sel;
	wire csr_mhpmcounter12_sel = csr_mode && (csr_addr == 12'hb0c);
	wire [31:0] csr_mhpmcounter12_value = csr_hpm_counter_value[384+:32];
	wire [31:0] csr_mhpmcounter12_wdata = csr_hpm_counter_wdata[384+:32];
	wire [31:0] csr_mhpmcounter12_next = csr_hpm_counter_next[384+:32];
	assign csr_hpm_counter_sel[12] = csr_mhpmcounter12_sel;
	wire csr_mhpmcounter13_sel = csr_mode && (csr_addr == 12'hb0d);
	wire [31:0] csr_mhpmcounter13_value = csr_hpm_counter_value[416+:32];
	wire [31:0] csr_mhpmcounter13_wdata = csr_hpm_counter_wdata[416+:32];
	wire [31:0] csr_mhpmcounter13_next = csr_hpm_counter_next[416+:32];
	assign csr_hpm_counter_sel[13] = csr_mhpmcounter13_sel;
	wire csr_mhpmcounter14_sel = csr_mode && (csr_addr == 12'hb0e);
	wire [31:0] csr_mhpmcounter14_value = csr_hpm_counter_value[448+:32];
	wire [31:0] csr_mhpmcounter14_wdata = csr_hpm_counter_wdata[448+:32];
	wire [31:0] csr_mhpmcounter14_next = csr_hpm_counter_next[448+:32];
	assign csr_hpm_counter_sel[14] = csr_mhpmcounter14_sel;
	wire csr_mhpmcounter15_sel = csr_mode && (csr_addr == 12'hb0f);
	wire [31:0] csr_mhpmcounter15_value = csr_hpm_counter_value[480+:32];
	wire [31:0] csr_mhpmcounter15_wdata = csr_hpm_counter_wdata[480+:32];
	wire [31:0] csr_mhpmcounter15_next = csr_hpm_counter_next[480+:32];
	assign csr_hpm_counter_sel[15] = csr_mhpmcounter15_sel;
	wire csr_mhpmcounter16_sel = csr_mode && (csr_addr == 12'hb10);
	wire [31:0] csr_mhpmcounter16_value = csr_hpm_counter_value[512+:32];
	wire [31:0] csr_mhpmcounter16_wdata = csr_hpm_counter_wdata[512+:32];
	wire [31:0] csr_mhpmcounter16_next = csr_hpm_counter_next[512+:32];
	assign csr_hpm_counter_sel[16] = csr_mhpmcounter16_sel;
	wire csr_mhpmcounter17_sel = csr_mode && (csr_addr == 12'hb11);
	wire [31:0] csr_mhpmcounter17_value = csr_hpm_counter_value[544+:32];
	wire [31:0] csr_mhpmcounter17_wdata = csr_hpm_counter_wdata[544+:32];
	wire [31:0] csr_mhpmcounter17_next = csr_hpm_counter_next[544+:32];
	assign csr_hpm_counter_sel[17] = csr_mhpmcounter17_sel;
	wire csr_mhpmcounter18_sel = csr_mode && (csr_addr == 12'hb12);
	wire [31:0] csr_mhpmcounter18_value = csr_hpm_counter_value[576+:32];
	wire [31:0] csr_mhpmcounter18_wdata = csr_hpm_counter_wdata[576+:32];
	wire [31:0] csr_mhpmcounter18_next = csr_hpm_counter_next[576+:32];
	assign csr_hpm_counter_sel[18] = csr_mhpmcounter18_sel;
	wire csr_mhpmcounter19_sel = csr_mode && (csr_addr == 12'hb13);
	wire [31:0] csr_mhpmcounter19_value = csr_hpm_counter_value[608+:32];
	wire [31:0] csr_mhpmcounter19_wdata = csr_hpm_counter_wdata[608+:32];
	wire [31:0] csr_mhpmcounter19_next = csr_hpm_counter_next[608+:32];
	assign csr_hpm_counter_sel[19] = csr_mhpmcounter19_sel;
	wire csr_mhpmcounter20_sel = csr_mode && (csr_addr == 12'hb14);
	wire [31:0] csr_mhpmcounter20_value = csr_hpm_counter_value[640+:32];
	wire [31:0] csr_mhpmcounter20_wdata = csr_hpm_counter_wdata[640+:32];
	wire [31:0] csr_mhpmcounter20_next = csr_hpm_counter_next[640+:32];
	assign csr_hpm_counter_sel[20] = csr_mhpmcounter20_sel;
	wire csr_mhpmcounter21_sel = csr_mode && (csr_addr == 12'hb15);
	wire [31:0] csr_mhpmcounter21_value = csr_hpm_counter_value[672+:32];
	wire [31:0] csr_mhpmcounter21_wdata = csr_hpm_counter_wdata[672+:32];
	wire [31:0] csr_mhpmcounter21_next = csr_hpm_counter_next[672+:32];
	assign csr_hpm_counter_sel[21] = csr_mhpmcounter21_sel;
	wire csr_mhpmcounter22_sel = csr_mode && (csr_addr == 12'hb16);
	wire [31:0] csr_mhpmcounter22_value = csr_hpm_counter_value[704+:32];
	wire [31:0] csr_mhpmcounter22_wdata = csr_hpm_counter_wdata[704+:32];
	wire [31:0] csr_mhpmcounter22_next = csr_hpm_counter_next[704+:32];
	assign csr_hpm_counter_sel[22] = csr_mhpmcounter22_sel;
	wire csr_mhpmcounter23_sel = csr_mode && (csr_addr == 12'hb17);
	wire [31:0] csr_mhpmcounter23_value = csr_hpm_counter_value[736+:32];
	wire [31:0] csr_mhpmcounter23_wdata = csr_hpm_counter_wdata[736+:32];
	wire [31:0] csr_mhpmcounter23_next = csr_hpm_counter_next[736+:32];
	assign csr_hpm_counter_sel[23] = csr_mhpmcounter23_sel;
	wire csr_mhpmcounter24_sel = csr_mode && (csr_addr == 12'hb18);
	wire [31:0] csr_mhpmcounter24_value = csr_hpm_counter_value[768+:32];
	wire [31:0] csr_mhpmcounter24_wdata = csr_hpm_counter_wdata[768+:32];
	wire [31:0] csr_mhpmcounter24_next = csr_hpm_counter_next[768+:32];
	assign csr_hpm_counter_sel[24] = csr_mhpmcounter24_sel;
	wire csr_mhpmcounter25_sel = csr_mode && (csr_addr == 12'hb19);
	wire [31:0] csr_mhpmcounter25_value = csr_hpm_counter_value[800+:32];
	wire [31:0] csr_mhpmcounter25_wdata = csr_hpm_counter_wdata[800+:32];
	wire [31:0] csr_mhpmcounter25_next = csr_hpm_counter_next[800+:32];
	assign csr_hpm_counter_sel[25] = csr_mhpmcounter25_sel;
	wire csr_mhpmcounter26_sel = csr_mode && (csr_addr == 12'hb1a);
	wire [31:0] csr_mhpmcounter26_value = csr_hpm_counter_value[832+:32];
	wire [31:0] csr_mhpmcounter26_wdata = csr_hpm_counter_wdata[832+:32];
	wire [31:0] csr_mhpmcounter26_next = csr_hpm_counter_next[832+:32];
	assign csr_hpm_counter_sel[26] = csr_mhpmcounter26_sel;
	wire csr_mhpmcounter27_sel = csr_mode && (csr_addr == 12'hb1b);
	wire [31:0] csr_mhpmcounter27_value = csr_hpm_counter_value[864+:32];
	wire [31:0] csr_mhpmcounter27_wdata = csr_hpm_counter_wdata[864+:32];
	wire [31:0] csr_mhpmcounter27_next = csr_hpm_counter_next[864+:32];
	assign csr_hpm_counter_sel[27] = csr_mhpmcounter27_sel;
	wire csr_mhpmcounter28_sel = csr_mode && (csr_addr == 12'hb1c);
	wire [31:0] csr_mhpmcounter28_value = csr_hpm_counter_value[896+:32];
	wire [31:0] csr_mhpmcounter28_wdata = csr_hpm_counter_wdata[896+:32];
	wire [31:0] csr_mhpmcounter28_next = csr_hpm_counter_next[896+:32];
	assign csr_hpm_counter_sel[28] = csr_mhpmcounter28_sel;
	wire csr_mhpmcounter29_sel = csr_mode && (csr_addr == 12'hb1d);
	wire [31:0] csr_mhpmcounter29_value = csr_hpm_counter_value[928+:32];
	wire [31:0] csr_mhpmcounter29_wdata = csr_hpm_counter_wdata[928+:32];
	wire [31:0] csr_mhpmcounter29_next = csr_hpm_counter_next[928+:32];
	assign csr_hpm_counter_sel[29] = csr_mhpmcounter29_sel;
	wire csr_mhpmcounter30_sel = csr_mode && (csr_addr == 12'hb1e);
	wire [31:0] csr_mhpmcounter30_value = csr_hpm_counter_value[960+:32];
	wire [31:0] csr_mhpmcounter30_wdata = csr_hpm_counter_wdata[960+:32];
	wire [31:0] csr_mhpmcounter30_next = csr_hpm_counter_next[960+:32];
	assign csr_hpm_counter_sel[30] = csr_mhpmcounter30_sel;
	wire csr_mhpmcounter31_sel = csr_mode && (csr_addr == 12'hb1f);
	wire [31:0] csr_mhpmcounter31_value = csr_hpm_counter_value[992+:32];
	wire [31:0] csr_mhpmcounter31_wdata = csr_hpm_counter_wdata[992+:32];
	wire [31:0] csr_mhpmcounter31_next = csr_hpm_counter_next[992+:32];
	assign csr_hpm_counter_sel[31] = csr_mhpmcounter31_sel;
	integer hpm_counterh_idx;
	wire [31:0] csr_hpm_counterh_sel;
	reg [1023:0] csr_hpm_counterh_value;
	reg [1023:0] csr_hpm_counterh_wdata;
	reg [1023:0] csr_hpm_counterh_next;
	always @(posedge clock) begin
		csr_hpm_counterh_value <= csr_hpm_counterh_next;
		if (reset || reset_q)
			csr_hpm_counterh_value <= 'b0;
	end
	wire csr_mcycleh_sel = csr_mode && (csr_addr == 12'hb80);
	wire [31:0] csr_mcycleh_value = csr_hpm_counterh_value[0+:32];
	wire [31:0] csr_mcycleh_wdata = csr_hpm_counterh_wdata[0+:32];
	wire [31:0] csr_mcycleh_next = csr_hpm_counterh_next[0+:32];
	assign csr_hpm_counterh_sel[0] = csr_mcycleh_sel;
	wire csr_minstreth_sel = csr_mode && (csr_addr == 12'hb82);
	wire [31:0] csr_minstreth_value = csr_hpm_counterh_value[64+:32];
	wire [31:0] csr_minstreth_wdata = csr_hpm_counterh_wdata[64+:32];
	wire [31:0] csr_minstreth_next = csr_hpm_counterh_next[64+:32];
	assign csr_hpm_counterh_sel[2] = csr_minstreth_sel;
	wire csr_mhpmcounter3h_sel = csr_mode && (csr_addr == 12'hb83);
	wire [31:0] csr_mhpmcounter3h_value = csr_hpm_counterh_value[96+:32];
	wire [31:0] csr_mhpmcounter3h_wdata = csr_hpm_counterh_wdata[96+:32];
	wire [31:0] csr_mhpmcounter3h_next = csr_hpm_counterh_next[96+:32];
	assign csr_hpm_counterh_sel[3] = csr_mhpmcounter3h_sel;
	wire csr_mhpmcounter4h_sel = csr_mode && (csr_addr == 12'hb84);
	wire [31:0] csr_mhpmcounter4h_value = csr_hpm_counterh_value[128+:32];
	wire [31:0] csr_mhpmcounter4h_wdata = csr_hpm_counterh_wdata[128+:32];
	wire [31:0] csr_mhpmcounter4h_next = csr_hpm_counterh_next[128+:32];
	assign csr_hpm_counterh_sel[4] = csr_mhpmcounter4h_sel;
	wire csr_mhpmcounter5h_sel = csr_mode && (csr_addr == 12'hb85);
	wire [31:0] csr_mhpmcounter5h_value = csr_hpm_counterh_value[160+:32];
	wire [31:0] csr_mhpmcounter5h_wdata = csr_hpm_counterh_wdata[160+:32];
	wire [31:0] csr_mhpmcounter5h_next = csr_hpm_counterh_next[160+:32];
	assign csr_hpm_counterh_sel[5] = csr_mhpmcounter5h_sel;
	wire csr_mhpmcounter6h_sel = csr_mode && (csr_addr == 12'hb86);
	wire [31:0] csr_mhpmcounter6h_value = csr_hpm_counterh_value[192+:32];
	wire [31:0] csr_mhpmcounter6h_wdata = csr_hpm_counterh_wdata[192+:32];
	wire [31:0] csr_mhpmcounter6h_next = csr_hpm_counterh_next[192+:32];
	assign csr_hpm_counterh_sel[6] = csr_mhpmcounter6h_sel;
	wire csr_mhpmcounter7h_sel = csr_mode && (csr_addr == 12'hb87);
	wire [31:0] csr_mhpmcounter7h_value = csr_hpm_counterh_value[224+:32];
	wire [31:0] csr_mhpmcounter7h_wdata = csr_hpm_counterh_wdata[224+:32];
	wire [31:0] csr_mhpmcounter7h_next = csr_hpm_counterh_next[224+:32];
	assign csr_hpm_counterh_sel[7] = csr_mhpmcounter7h_sel;
	wire csr_mhpmcounter8h_sel = csr_mode && (csr_addr == 12'hb88);
	wire [31:0] csr_mhpmcounter8h_value = csr_hpm_counterh_value[256+:32];
	wire [31:0] csr_mhpmcounter8h_wdata = csr_hpm_counterh_wdata[256+:32];
	wire [31:0] csr_mhpmcounter8h_next = csr_hpm_counterh_next[256+:32];
	assign csr_hpm_counterh_sel[8] = csr_mhpmcounter8h_sel;
	wire csr_mhpmcounter9h_sel = csr_mode && (csr_addr == 12'hb89);
	wire [31:0] csr_mhpmcounter9h_value = csr_hpm_counterh_value[288+:32];
	wire [31:0] csr_mhpmcounter9h_wdata = csr_hpm_counterh_wdata[288+:32];
	wire [31:0] csr_mhpmcounter9h_next = csr_hpm_counterh_next[288+:32];
	assign csr_hpm_counterh_sel[9] = csr_mhpmcounter9h_sel;
	wire csr_mhpmcounter10h_sel = csr_mode && (csr_addr == 12'hb8a);
	wire [31:0] csr_mhpmcounter10h_value = csr_hpm_counterh_value[320+:32];
	wire [31:0] csr_mhpmcounter10h_wdata = csr_hpm_counterh_wdata[320+:32];
	wire [31:0] csr_mhpmcounter10h_next = csr_hpm_counterh_next[320+:32];
	assign csr_hpm_counterh_sel[10] = csr_mhpmcounter10h_sel;
	wire csr_mhpmcounter11h_sel = csr_mode && (csr_addr == 12'hb8b);
	wire [31:0] csr_mhpmcounter11h_value = csr_hpm_counterh_value[352+:32];
	wire [31:0] csr_mhpmcounter11h_wdata = csr_hpm_counterh_wdata[352+:32];
	wire [31:0] csr_mhpmcounter11h_next = csr_hpm_counterh_next[352+:32];
	assign csr_hpm_counterh_sel[11] = csr_mhpmcounter11h_sel;
	wire csr_mhpmcounter12h_sel = csr_mode && (csr_addr == 12'hb8c);
	wire [31:0] csr_mhpmcounter12h_value = csr_hpm_counterh_value[384+:32];
	wire [31:0] csr_mhpmcounter12h_wdata = csr_hpm_counterh_wdata[384+:32];
	wire [31:0] csr_mhpmcounter12h_next = csr_hpm_counterh_next[384+:32];
	assign csr_hpm_counterh_sel[12] = csr_mhpmcounter12h_sel;
	wire csr_mhpmcounter13h_sel = csr_mode && (csr_addr == 12'hb8d);
	wire [31:0] csr_mhpmcounter13h_value = csr_hpm_counterh_value[416+:32];
	wire [31:0] csr_mhpmcounter13h_wdata = csr_hpm_counterh_wdata[416+:32];
	wire [31:0] csr_mhpmcounter13h_next = csr_hpm_counterh_next[416+:32];
	assign csr_hpm_counterh_sel[13] = csr_mhpmcounter13h_sel;
	wire csr_mhpmcounter14h_sel = csr_mode && (csr_addr == 12'hb8e);
	wire [31:0] csr_mhpmcounter14h_value = csr_hpm_counterh_value[448+:32];
	wire [31:0] csr_mhpmcounter14h_wdata = csr_hpm_counterh_wdata[448+:32];
	wire [31:0] csr_mhpmcounter14h_next = csr_hpm_counterh_next[448+:32];
	assign csr_hpm_counterh_sel[14] = csr_mhpmcounter14h_sel;
	wire csr_mhpmcounter15h_sel = csr_mode && (csr_addr == 12'hb8f);
	wire [31:0] csr_mhpmcounter15h_value = csr_hpm_counterh_value[480+:32];
	wire [31:0] csr_mhpmcounter15h_wdata = csr_hpm_counterh_wdata[480+:32];
	wire [31:0] csr_mhpmcounter15h_next = csr_hpm_counterh_next[480+:32];
	assign csr_hpm_counterh_sel[15] = csr_mhpmcounter15h_sel;
	wire csr_mhpmcounter16h_sel = csr_mode && (csr_addr == 12'hb90);
	wire [31:0] csr_mhpmcounter16h_value = csr_hpm_counterh_value[512+:32];
	wire [31:0] csr_mhpmcounter16h_wdata = csr_hpm_counterh_wdata[512+:32];
	wire [31:0] csr_mhpmcounter16h_next = csr_hpm_counterh_next[512+:32];
	assign csr_hpm_counterh_sel[16] = csr_mhpmcounter16h_sel;
	wire csr_mhpmcounter17h_sel = csr_mode && (csr_addr == 12'hb91);
	wire [31:0] csr_mhpmcounter17h_value = csr_hpm_counterh_value[544+:32];
	wire [31:0] csr_mhpmcounter17h_wdata = csr_hpm_counterh_wdata[544+:32];
	wire [31:0] csr_mhpmcounter17h_next = csr_hpm_counterh_next[544+:32];
	assign csr_hpm_counterh_sel[17] = csr_mhpmcounter17h_sel;
	wire csr_mhpmcounter18h_sel = csr_mode && (csr_addr == 12'hb92);
	wire [31:0] csr_mhpmcounter18h_value = csr_hpm_counterh_value[576+:32];
	wire [31:0] csr_mhpmcounter18h_wdata = csr_hpm_counterh_wdata[576+:32];
	wire [31:0] csr_mhpmcounter18h_next = csr_hpm_counterh_next[576+:32];
	assign csr_hpm_counterh_sel[18] = csr_mhpmcounter18h_sel;
	wire csr_mhpmcounter19h_sel = csr_mode && (csr_addr == 12'hb93);
	wire [31:0] csr_mhpmcounter19h_value = csr_hpm_counterh_value[608+:32];
	wire [31:0] csr_mhpmcounter19h_wdata = csr_hpm_counterh_wdata[608+:32];
	wire [31:0] csr_mhpmcounter19h_next = csr_hpm_counterh_next[608+:32];
	assign csr_hpm_counterh_sel[19] = csr_mhpmcounter19h_sel;
	wire csr_mhpmcounter20h_sel = csr_mode && (csr_addr == 12'hb94);
	wire [31:0] csr_mhpmcounter20h_value = csr_hpm_counterh_value[640+:32];
	wire [31:0] csr_mhpmcounter20h_wdata = csr_hpm_counterh_wdata[640+:32];
	wire [31:0] csr_mhpmcounter20h_next = csr_hpm_counterh_next[640+:32];
	assign csr_hpm_counterh_sel[20] = csr_mhpmcounter20h_sel;
	wire csr_mhpmcounter21h_sel = csr_mode && (csr_addr == 12'hb95);
	wire [31:0] csr_mhpmcounter21h_value = csr_hpm_counterh_value[672+:32];
	wire [31:0] csr_mhpmcounter21h_wdata = csr_hpm_counterh_wdata[672+:32];
	wire [31:0] csr_mhpmcounter21h_next = csr_hpm_counterh_next[672+:32];
	assign csr_hpm_counterh_sel[21] = csr_mhpmcounter21h_sel;
	wire csr_mhpmcounter22h_sel = csr_mode && (csr_addr == 12'hb96);
	wire [31:0] csr_mhpmcounter22h_value = csr_hpm_counterh_value[704+:32];
	wire [31:0] csr_mhpmcounter22h_wdata = csr_hpm_counterh_wdata[704+:32];
	wire [31:0] csr_mhpmcounter22h_next = csr_hpm_counterh_next[704+:32];
	assign csr_hpm_counterh_sel[22] = csr_mhpmcounter22h_sel;
	wire csr_mhpmcounter23h_sel = csr_mode && (csr_addr == 12'hb97);
	wire [31:0] csr_mhpmcounter23h_value = csr_hpm_counterh_value[736+:32];
	wire [31:0] csr_mhpmcounter23h_wdata = csr_hpm_counterh_wdata[736+:32];
	wire [31:0] csr_mhpmcounter23h_next = csr_hpm_counterh_next[736+:32];
	assign csr_hpm_counterh_sel[23] = csr_mhpmcounter23h_sel;
	wire csr_mhpmcounter24h_sel = csr_mode && (csr_addr == 12'hb98);
	wire [31:0] csr_mhpmcounter24h_value = csr_hpm_counterh_value[768+:32];
	wire [31:0] csr_mhpmcounter24h_wdata = csr_hpm_counterh_wdata[768+:32];
	wire [31:0] csr_mhpmcounter24h_next = csr_hpm_counterh_next[768+:32];
	assign csr_hpm_counterh_sel[24] = csr_mhpmcounter24h_sel;
	wire csr_mhpmcounter25h_sel = csr_mode && (csr_addr == 12'hb99);
	wire [31:0] csr_mhpmcounter25h_value = csr_hpm_counterh_value[800+:32];
	wire [31:0] csr_mhpmcounter25h_wdata = csr_hpm_counterh_wdata[800+:32];
	wire [31:0] csr_mhpmcounter25h_next = csr_hpm_counterh_next[800+:32];
	assign csr_hpm_counterh_sel[25] = csr_mhpmcounter25h_sel;
	wire csr_mhpmcounter26h_sel = csr_mode && (csr_addr == 12'hb9a);
	wire [31:0] csr_mhpmcounter26h_value = csr_hpm_counterh_value[832+:32];
	wire [31:0] csr_mhpmcounter26h_wdata = csr_hpm_counterh_wdata[832+:32];
	wire [31:0] csr_mhpmcounter26h_next = csr_hpm_counterh_next[832+:32];
	assign csr_hpm_counterh_sel[26] = csr_mhpmcounter26h_sel;
	wire csr_mhpmcounter27h_sel = csr_mode && (csr_addr == 12'hb9b);
	wire [31:0] csr_mhpmcounter27h_value = csr_hpm_counterh_value[864+:32];
	wire [31:0] csr_mhpmcounter27h_wdata = csr_hpm_counterh_wdata[864+:32];
	wire [31:0] csr_mhpmcounter27h_next = csr_hpm_counterh_next[864+:32];
	assign csr_hpm_counterh_sel[27] = csr_mhpmcounter27h_sel;
	wire csr_mhpmcounter28h_sel = csr_mode && (csr_addr == 12'hb9c);
	wire [31:0] csr_mhpmcounter28h_value = csr_hpm_counterh_value[896+:32];
	wire [31:0] csr_mhpmcounter28h_wdata = csr_hpm_counterh_wdata[896+:32];
	wire [31:0] csr_mhpmcounter28h_next = csr_hpm_counterh_next[896+:32];
	assign csr_hpm_counterh_sel[28] = csr_mhpmcounter28h_sel;
	wire csr_mhpmcounter29h_sel = csr_mode && (csr_addr == 12'hb9d);
	wire [31:0] csr_mhpmcounter29h_value = csr_hpm_counterh_value[928+:32];
	wire [31:0] csr_mhpmcounter29h_wdata = csr_hpm_counterh_wdata[928+:32];
	wire [31:0] csr_mhpmcounter29h_next = csr_hpm_counterh_next[928+:32];
	assign csr_hpm_counterh_sel[29] = csr_mhpmcounter29h_sel;
	wire csr_mhpmcounter30h_sel = csr_mode && (csr_addr == 12'hb9e);
	wire [31:0] csr_mhpmcounter30h_value = csr_hpm_counterh_value[960+:32];
	wire [31:0] csr_mhpmcounter30h_wdata = csr_hpm_counterh_wdata[960+:32];
	wire [31:0] csr_mhpmcounter30h_next = csr_hpm_counterh_next[960+:32];
	assign csr_hpm_counterh_sel[30] = csr_mhpmcounter30h_sel;
	wire csr_mhpmcounter31h_sel = csr_mode && (csr_addr == 12'hb9f);
	wire [31:0] csr_mhpmcounter31h_value = csr_hpm_counterh_value[992+:32];
	wire [31:0] csr_mhpmcounter31h_wdata = csr_hpm_counterh_wdata[992+:32];
	wire [31:0] csr_mhpmcounter31h_next = csr_hpm_counterh_next[992+:32];
	assign csr_hpm_counterh_sel[31] = csr_mhpmcounter31h_sel;
	integer hpm_event_idx;
	wire [31:0] csr_hpm_event_sel;
	reg [1023:0] csr_hpm_event_value;
	reg [1023:0] csr_hpm_event_wdata;
	reg [1023:0] csr_hpm_event_next;
	always @(posedge clock) begin
		csr_hpm_event_value <= csr_hpm_event_next;
		if (reset || reset_q)
			csr_hpm_event_value <= 'b0;
	end
	wire csr_mhpmevent3_sel = csr_mode && (csr_addr == 12'h323);
	wire [31:0] csr_mhpmevent3_value = csr_hpm_event_value[96+:32];
	wire [31:0] csr_mhpmevent3_wdata = csr_hpm_event_wdata[96+:32];
	wire [31:0] csr_mhpmevent3_next = csr_hpm_event_next[96+:32];
	assign csr_hpm_event_sel[3] = csr_mhpmevent3_sel;
	wire csr_mhpmevent4_sel = csr_mode && (csr_addr == 12'h324);
	wire [31:0] csr_mhpmevent4_value = csr_hpm_event_value[128+:32];
	wire [31:0] csr_mhpmevent4_wdata = csr_hpm_event_wdata[128+:32];
	wire [31:0] csr_mhpmevent4_next = csr_hpm_event_next[128+:32];
	assign csr_hpm_event_sel[4] = csr_mhpmevent4_sel;
	wire csr_mhpmevent5_sel = csr_mode && (csr_addr == 12'h325);
	wire [31:0] csr_mhpmevent5_value = csr_hpm_event_value[160+:32];
	wire [31:0] csr_mhpmevent5_wdata = csr_hpm_event_wdata[160+:32];
	wire [31:0] csr_mhpmevent5_next = csr_hpm_event_next[160+:32];
	assign csr_hpm_event_sel[5] = csr_mhpmevent5_sel;
	wire csr_mhpmevent6_sel = csr_mode && (csr_addr == 12'h326);
	wire [31:0] csr_mhpmevent6_value = csr_hpm_event_value[192+:32];
	wire [31:0] csr_mhpmevent6_wdata = csr_hpm_event_wdata[192+:32];
	wire [31:0] csr_mhpmevent6_next = csr_hpm_event_next[192+:32];
	assign csr_hpm_event_sel[6] = csr_mhpmevent6_sel;
	wire csr_mhpmevent7_sel = csr_mode && (csr_addr == 12'h327);
	wire [31:0] csr_mhpmevent7_value = csr_hpm_event_value[224+:32];
	wire [31:0] csr_mhpmevent7_wdata = csr_hpm_event_wdata[224+:32];
	wire [31:0] csr_mhpmevent7_next = csr_hpm_event_next[224+:32];
	assign csr_hpm_event_sel[7] = csr_mhpmevent7_sel;
	wire csr_mhpmevent8_sel = csr_mode && (csr_addr == 12'h328);
	wire [31:0] csr_mhpmevent8_value = csr_hpm_event_value[256+:32];
	wire [31:0] csr_mhpmevent8_wdata = csr_hpm_event_wdata[256+:32];
	wire [31:0] csr_mhpmevent8_next = csr_hpm_event_next[256+:32];
	assign csr_hpm_event_sel[8] = csr_mhpmevent8_sel;
	wire csr_mhpmevent9_sel = csr_mode && (csr_addr == 12'h329);
	wire [31:0] csr_mhpmevent9_value = csr_hpm_event_value[288+:32];
	wire [31:0] csr_mhpmevent9_wdata = csr_hpm_event_wdata[288+:32];
	wire [31:0] csr_mhpmevent9_next = csr_hpm_event_next[288+:32];
	assign csr_hpm_event_sel[9] = csr_mhpmevent9_sel;
	wire csr_mhpmevent10_sel = csr_mode && (csr_addr == 12'h32a);
	wire [31:0] csr_mhpmevent10_value = csr_hpm_event_value[320+:32];
	wire [31:0] csr_mhpmevent10_wdata = csr_hpm_event_wdata[320+:32];
	wire [31:0] csr_mhpmevent10_next = csr_hpm_event_next[320+:32];
	assign csr_hpm_event_sel[10] = csr_mhpmevent10_sel;
	wire csr_mhpmevent11_sel = csr_mode && (csr_addr == 12'h32b);
	wire [31:0] csr_mhpmevent11_value = csr_hpm_event_value[352+:32];
	wire [31:0] csr_mhpmevent11_wdata = csr_hpm_event_wdata[352+:32];
	wire [31:0] csr_mhpmevent11_next = csr_hpm_event_next[352+:32];
	assign csr_hpm_event_sel[11] = csr_mhpmevent11_sel;
	wire csr_mhpmevent12_sel = csr_mode && (csr_addr == 12'h32c);
	wire [31:0] csr_mhpmevent12_value = csr_hpm_event_value[384+:32];
	wire [31:0] csr_mhpmevent12_wdata = csr_hpm_event_wdata[384+:32];
	wire [31:0] csr_mhpmevent12_next = csr_hpm_event_next[384+:32];
	assign csr_hpm_event_sel[12] = csr_mhpmevent12_sel;
	wire csr_mhpmevent13_sel = csr_mode && (csr_addr == 12'h32d);
	wire [31:0] csr_mhpmevent13_value = csr_hpm_event_value[416+:32];
	wire [31:0] csr_mhpmevent13_wdata = csr_hpm_event_wdata[416+:32];
	wire [31:0] csr_mhpmevent13_next = csr_hpm_event_next[416+:32];
	assign csr_hpm_event_sel[13] = csr_mhpmevent13_sel;
	wire csr_mhpmevent14_sel = csr_mode && (csr_addr == 12'h32e);
	wire [31:0] csr_mhpmevent14_value = csr_hpm_event_value[448+:32];
	wire [31:0] csr_mhpmevent14_wdata = csr_hpm_event_wdata[448+:32];
	wire [31:0] csr_mhpmevent14_next = csr_hpm_event_next[448+:32];
	assign csr_hpm_event_sel[14] = csr_mhpmevent14_sel;
	wire csr_mhpmevent15_sel = csr_mode && (csr_addr == 12'h32f);
	wire [31:0] csr_mhpmevent15_value = csr_hpm_event_value[480+:32];
	wire [31:0] csr_mhpmevent15_wdata = csr_hpm_event_wdata[480+:32];
	wire [31:0] csr_mhpmevent15_next = csr_hpm_event_next[480+:32];
	assign csr_hpm_event_sel[15] = csr_mhpmevent15_sel;
	wire csr_mhpmevent16_sel = csr_mode && (csr_addr == 12'h330);
	wire [31:0] csr_mhpmevent16_value = csr_hpm_event_value[512+:32];
	wire [31:0] csr_mhpmevent16_wdata = csr_hpm_event_wdata[512+:32];
	wire [31:0] csr_mhpmevent16_next = csr_hpm_event_next[512+:32];
	assign csr_hpm_event_sel[16] = csr_mhpmevent16_sel;
	wire csr_mhpmevent17_sel = csr_mode && (csr_addr == 12'h331);
	wire [31:0] csr_mhpmevent17_value = csr_hpm_event_value[544+:32];
	wire [31:0] csr_mhpmevent17_wdata = csr_hpm_event_wdata[544+:32];
	wire [31:0] csr_mhpmevent17_next = csr_hpm_event_next[544+:32];
	assign csr_hpm_event_sel[17] = csr_mhpmevent17_sel;
	wire csr_mhpmevent18_sel = csr_mode && (csr_addr == 12'h332);
	wire [31:0] csr_mhpmevent18_value = csr_hpm_event_value[576+:32];
	wire [31:0] csr_mhpmevent18_wdata = csr_hpm_event_wdata[576+:32];
	wire [31:0] csr_mhpmevent18_next = csr_hpm_event_next[576+:32];
	assign csr_hpm_event_sel[18] = csr_mhpmevent18_sel;
	wire csr_mhpmevent19_sel = csr_mode && (csr_addr == 12'h333);
	wire [31:0] csr_mhpmevent19_value = csr_hpm_event_value[608+:32];
	wire [31:0] csr_mhpmevent19_wdata = csr_hpm_event_wdata[608+:32];
	wire [31:0] csr_mhpmevent19_next = csr_hpm_event_next[608+:32];
	assign csr_hpm_event_sel[19] = csr_mhpmevent19_sel;
	wire csr_mhpmevent20_sel = csr_mode && (csr_addr == 12'h334);
	wire [31:0] csr_mhpmevent20_value = csr_hpm_event_value[640+:32];
	wire [31:0] csr_mhpmevent20_wdata = csr_hpm_event_wdata[640+:32];
	wire [31:0] csr_mhpmevent20_next = csr_hpm_event_next[640+:32];
	assign csr_hpm_event_sel[20] = csr_mhpmevent20_sel;
	wire csr_mhpmevent21_sel = csr_mode && (csr_addr == 12'h335);
	wire [31:0] csr_mhpmevent21_value = csr_hpm_event_value[672+:32];
	wire [31:0] csr_mhpmevent21_wdata = csr_hpm_event_wdata[672+:32];
	wire [31:0] csr_mhpmevent21_next = csr_hpm_event_next[672+:32];
	assign csr_hpm_event_sel[21] = csr_mhpmevent21_sel;
	wire csr_mhpmevent22_sel = csr_mode && (csr_addr == 12'h336);
	wire [31:0] csr_mhpmevent22_value = csr_hpm_event_value[704+:32];
	wire [31:0] csr_mhpmevent22_wdata = csr_hpm_event_wdata[704+:32];
	wire [31:0] csr_mhpmevent22_next = csr_hpm_event_next[704+:32];
	assign csr_hpm_event_sel[22] = csr_mhpmevent22_sel;
	wire csr_mhpmevent23_sel = csr_mode && (csr_addr == 12'h337);
	wire [31:0] csr_mhpmevent23_value = csr_hpm_event_value[736+:32];
	wire [31:0] csr_mhpmevent23_wdata = csr_hpm_event_wdata[736+:32];
	wire [31:0] csr_mhpmevent23_next = csr_hpm_event_next[736+:32];
	assign csr_hpm_event_sel[23] = csr_mhpmevent23_sel;
	wire csr_mhpmevent24_sel = csr_mode && (csr_addr == 12'h338);
	wire [31:0] csr_mhpmevent24_value = csr_hpm_event_value[768+:32];
	wire [31:0] csr_mhpmevent24_wdata = csr_hpm_event_wdata[768+:32];
	wire [31:0] csr_mhpmevent24_next = csr_hpm_event_next[768+:32];
	assign csr_hpm_event_sel[24] = csr_mhpmevent24_sel;
	wire csr_mhpmevent25_sel = csr_mode && (csr_addr == 12'h339);
	wire [31:0] csr_mhpmevent25_value = csr_hpm_event_value[800+:32];
	wire [31:0] csr_mhpmevent25_wdata = csr_hpm_event_wdata[800+:32];
	wire [31:0] csr_mhpmevent25_next = csr_hpm_event_next[800+:32];
	assign csr_hpm_event_sel[25] = csr_mhpmevent25_sel;
	wire csr_mhpmevent26_sel = csr_mode && (csr_addr == 12'h33a);
	wire [31:0] csr_mhpmevent26_value = csr_hpm_event_value[832+:32];
	wire [31:0] csr_mhpmevent26_wdata = csr_hpm_event_wdata[832+:32];
	wire [31:0] csr_mhpmevent26_next = csr_hpm_event_next[832+:32];
	assign csr_hpm_event_sel[26] = csr_mhpmevent26_sel;
	wire csr_mhpmevent27_sel = csr_mode && (csr_addr == 12'h33b);
	wire [31:0] csr_mhpmevent27_value = csr_hpm_event_value[864+:32];
	wire [31:0] csr_mhpmevent27_wdata = csr_hpm_event_wdata[864+:32];
	wire [31:0] csr_mhpmevent27_next = csr_hpm_event_next[864+:32];
	assign csr_hpm_event_sel[27] = csr_mhpmevent27_sel;
	wire csr_mhpmevent28_sel = csr_mode && (csr_addr == 12'h33c);
	wire [31:0] csr_mhpmevent28_value = csr_hpm_event_value[896+:32];
	wire [31:0] csr_mhpmevent28_wdata = csr_hpm_event_wdata[896+:32];
	wire [31:0] csr_mhpmevent28_next = csr_hpm_event_next[896+:32];
	assign csr_hpm_event_sel[28] = csr_mhpmevent28_sel;
	wire csr_mhpmevent29_sel = csr_mode && (csr_addr == 12'h33d);
	wire [31:0] csr_mhpmevent29_value = csr_hpm_event_value[928+:32];
	wire [31:0] csr_mhpmevent29_wdata = csr_hpm_event_wdata[928+:32];
	wire [31:0] csr_mhpmevent29_next = csr_hpm_event_next[928+:32];
	assign csr_hpm_event_sel[29] = csr_mhpmevent29_sel;
	wire csr_mhpmevent30_sel = csr_mode && (csr_addr == 12'h33e);
	wire [31:0] csr_mhpmevent30_value = csr_hpm_event_value[960+:32];
	wire [31:0] csr_mhpmevent30_wdata = csr_hpm_event_wdata[960+:32];
	wire [31:0] csr_mhpmevent30_next = csr_hpm_event_next[960+:32];
	assign csr_hpm_event_sel[30] = csr_mhpmevent30_sel;
	wire csr_mhpmevent31_sel = csr_mode && (csr_addr == 12'h33f);
	wire [31:0] csr_mhpmevent31_value = csr_hpm_event_value[992+:32];
	wire [31:0] csr_mhpmevent31_wdata = csr_hpm_event_wdata[992+:32];
	wire [31:0] csr_mhpmevent31_next = csr_hpm_event_next[992+:32];
	assign csr_hpm_event_sel[31] = csr_mhpmevent31_sel;
	wire csr_custom_sel = csr_mode && (csr_addr == 12'hbc0);
	reg [31:0] csr_custom_value;
	reg [31:0] csr_custom_wdata;
	reg [31:0] csr_custom_next;
	always @(posedge clock) begin
		csr_custom_value <= csr_custom_next;
		if (reset || reset_q)
			csr_custom_value <= 32'h00000000;
	end
	wire csr_custom_ro_sel = csr_ro && (csr_addr == 12'hfc0);
	localparam [31:0] csr_custom_ro_value = 32'hdeadbeef;
	assign csr_hpm_event_sel[2:0] = 0;
	assign csr_hpm_counter_sel[1] = 0;
	assign csr_hpm_counterh_sel[1] = 0;
	wire [31:0] irq_en;
	assign irq_en = irq & csr_mie_value;
	always @(*)
		if (irq_en[31])
			irq_num = 5'd31;
		else if (irq_en[30])
			irq_num = 5'd30;
		else if (irq_en[29])
			irq_num = 5'd29;
		else if (irq_en[28])
			irq_num = 5'd28;
		else if (irq_en[27])
			irq_num = 5'd27;
		else if (irq_en[26])
			irq_num = 5'd26;
		else if (irq_en[25])
			irq_num = 5'd25;
		else if (irq_en[24])
			irq_num = 5'd24;
		else if (irq_en[23])
			irq_num = 5'd23;
		else if (irq_en[22])
			irq_num = 5'd22;
		else if (irq_en[21])
			irq_num = 5'd21;
		else if (irq_en[20])
			irq_num = 5'd20;
		else if (irq_en[19])
			irq_num = 5'd19;
		else if (irq_en[18])
			irq_num = 5'd18;
		else if (irq_en[17])
			irq_num = 5'd17;
		else if (irq_en[16])
			irq_num = 5'd16;
		else if (irq_en[11])
			irq_num = 5'd11;
		else if (irq_en[7])
			irq_num = 5'd7;
		else if (irq_en[3])
			irq_num = 5'd3;
		else
			irq_num = 5'd0;
	always @(*) begin
		npc = pc + 4;
		next_wr = 0;
		next_rd = 0;
		cycle_intr = 0;
		cycle_trap = 0;
		cycle_insn = 0;
		cycle_late_wr = 0;
		wr_rd = insn_rd;
		illinsn = 0;
		mem_wr_enable = 0;
		mem_wr_addr = 32'hxxxxxxxx;
		mem_wr_data = 32'hxxxxxxxx;
		mem_wr_strb = 4'hx;
		mem_rd_enable = 0;
		mem_rd_addr = 32'hxxxxxxxx;
		mem_rd_reg = 5'hxx;
		mem_rd_func = 5'hxx;
		csr_ack = 0;
		csr_rdval = 'hx;
		(* full_case, parallel_case *)
		case (1'b1)
			csr_ro && csr_mvendorid_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mvendorid_value;
			end
			csr_ro && csr_marchid_sel: begin
				csr_ack = 1;
				csr_rdval = csr_marchid_value;
			end
			csr_ro && csr_mimpid_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mimpid_value;
			end
			csr_ro && csr_mhartid_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhartid_value;
			end
			csr_ro && csr_mconfigptr_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mconfigptr_value;
			end
			csr_mode && csr_mstatus_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mstatus_value;
			end
			csr_mode && csr_misa_sel: begin
				csr_ack = 1;
				csr_rdval = csr_misa_value;
			end
			csr_mode && csr_mie_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mie_value;
			end
			csr_mode && csr_mtvec_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mtvec_value;
			end
			csr_mode && csr_mstatush_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mstatush_value;
			end
			csr_mode && csr_mscratch_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mscratch_value;
			end
			csr_mode && csr_mepc_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mepc_value;
			end
			csr_mode && csr_mcause_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mcause_value;
			end
			csr_mode && csr_mtval_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mtval_value;
			end
			csr_mode && csr_mip_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mip_value;
			end
			csr_mode && csr_mcycle_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mcycle_value;
			end
			csr_mode && csr_minstret_sel: begin
				csr_ack = 1;
				csr_rdval = csr_minstret_value;
			end
			csr_mode && csr_mhpmcounter3_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter3_value;
			end
			csr_mode && csr_mhpmcounter4_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter4_value;
			end
			csr_mode && csr_mhpmcounter5_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter5_value;
			end
			csr_mode && csr_mhpmcounter6_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter6_value;
			end
			csr_mode && csr_mhpmcounter7_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter7_value;
			end
			csr_mode && csr_mhpmcounter8_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter8_value;
			end
			csr_mode && csr_mhpmcounter9_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter9_value;
			end
			csr_mode && csr_mhpmcounter10_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter10_value;
			end
			csr_mode && csr_mhpmcounter11_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter11_value;
			end
			csr_mode && csr_mhpmcounter12_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter12_value;
			end
			csr_mode && csr_mhpmcounter13_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter13_value;
			end
			csr_mode && csr_mhpmcounter14_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter14_value;
			end
			csr_mode && csr_mhpmcounter15_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter15_value;
			end
			csr_mode && csr_mhpmcounter16_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter16_value;
			end
			csr_mode && csr_mhpmcounter17_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter17_value;
			end
			csr_mode && csr_mhpmcounter18_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter18_value;
			end
			csr_mode && csr_mhpmcounter19_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter19_value;
			end
			csr_mode && csr_mhpmcounter20_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter20_value;
			end
			csr_mode && csr_mhpmcounter21_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter21_value;
			end
			csr_mode && csr_mhpmcounter22_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter22_value;
			end
			csr_mode && csr_mhpmcounter23_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter23_value;
			end
			csr_mode && csr_mhpmcounter24_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter24_value;
			end
			csr_mode && csr_mhpmcounter25_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter25_value;
			end
			csr_mode && csr_mhpmcounter26_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter26_value;
			end
			csr_mode && csr_mhpmcounter27_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter27_value;
			end
			csr_mode && csr_mhpmcounter28_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter28_value;
			end
			csr_mode && csr_mhpmcounter29_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter29_value;
			end
			csr_mode && csr_mhpmcounter30_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter30_value;
			end
			csr_mode && csr_mhpmcounter31_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter31_value;
			end
			csr_mode && csr_mcycleh_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mcycleh_value;
			end
			csr_mode && csr_minstreth_sel: begin
				csr_ack = 1;
				csr_rdval = csr_minstreth_value;
			end
			csr_mode && csr_mhpmcounter3h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter3h_value;
			end
			csr_mode && csr_mhpmcounter4h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter4h_value;
			end
			csr_mode && csr_mhpmcounter5h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter5h_value;
			end
			csr_mode && csr_mhpmcounter6h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter6h_value;
			end
			csr_mode && csr_mhpmcounter7h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter7h_value;
			end
			csr_mode && csr_mhpmcounter8h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter8h_value;
			end
			csr_mode && csr_mhpmcounter9h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter9h_value;
			end
			csr_mode && csr_mhpmcounter10h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter10h_value;
			end
			csr_mode && csr_mhpmcounter11h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter11h_value;
			end
			csr_mode && csr_mhpmcounter12h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter12h_value;
			end
			csr_mode && csr_mhpmcounter13h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter13h_value;
			end
			csr_mode && csr_mhpmcounter14h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter14h_value;
			end
			csr_mode && csr_mhpmcounter15h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter15h_value;
			end
			csr_mode && csr_mhpmcounter16h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter16h_value;
			end
			csr_mode && csr_mhpmcounter17h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter17h_value;
			end
			csr_mode && csr_mhpmcounter18h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter18h_value;
			end
			csr_mode && csr_mhpmcounter19h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter19h_value;
			end
			csr_mode && csr_mhpmcounter20h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter20h_value;
			end
			csr_mode && csr_mhpmcounter21h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter21h_value;
			end
			csr_mode && csr_mhpmcounter22h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter22h_value;
			end
			csr_mode && csr_mhpmcounter23h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter23h_value;
			end
			csr_mode && csr_mhpmcounter24h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter24h_value;
			end
			csr_mode && csr_mhpmcounter25h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter25h_value;
			end
			csr_mode && csr_mhpmcounter26h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter26h_value;
			end
			csr_mode && csr_mhpmcounter27h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter27h_value;
			end
			csr_mode && csr_mhpmcounter28h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter28h_value;
			end
			csr_mode && csr_mhpmcounter29h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter29h_value;
			end
			csr_mode && csr_mhpmcounter30h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter30h_value;
			end
			csr_mode && csr_mhpmcounter31h_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmcounter31h_value;
			end
			csr_mode && csr_mhpmevent3_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent3_value;
			end
			csr_mode && csr_mhpmevent4_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent4_value;
			end
			csr_mode && csr_mhpmevent5_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent5_value;
			end
			csr_mode && csr_mhpmevent6_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent6_value;
			end
			csr_mode && csr_mhpmevent7_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent7_value;
			end
			csr_mode && csr_mhpmevent8_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent8_value;
			end
			csr_mode && csr_mhpmevent9_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent9_value;
			end
			csr_mode && csr_mhpmevent10_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent10_value;
			end
			csr_mode && csr_mhpmevent11_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent11_value;
			end
			csr_mode && csr_mhpmevent12_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent12_value;
			end
			csr_mode && csr_mhpmevent13_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent13_value;
			end
			csr_mode && csr_mhpmevent14_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent14_value;
			end
			csr_mode && csr_mhpmevent15_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent15_value;
			end
			csr_mode && csr_mhpmevent16_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent16_value;
			end
			csr_mode && csr_mhpmevent17_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent17_value;
			end
			csr_mode && csr_mhpmevent18_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent18_value;
			end
			csr_mode && csr_mhpmevent19_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent19_value;
			end
			csr_mode && csr_mhpmevent20_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent20_value;
			end
			csr_mode && csr_mhpmevent21_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent21_value;
			end
			csr_mode && csr_mhpmevent22_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent22_value;
			end
			csr_mode && csr_mhpmevent23_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent23_value;
			end
			csr_mode && csr_mhpmevent24_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent24_value;
			end
			csr_mode && csr_mhpmevent25_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent25_value;
			end
			csr_mode && csr_mhpmevent26_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent26_value;
			end
			csr_mode && csr_mhpmevent27_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent27_value;
			end
			csr_mode && csr_mhpmevent28_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent28_value;
			end
			csr_mode && csr_mhpmevent29_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent29_value;
			end
			csr_mode && csr_mhpmevent30_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent30_value;
			end
			csr_mode && csr_mhpmevent31_sel: begin
				csr_ack = 1;
				csr_rdval = csr_mhpmevent31_value;
			end
			csr_mode && csr_custom_sel: begin
				csr_ack = 1;
				csr_rdval = csr_custom_value;
			end
			csr_ro && csr_custom_ro_sel: begin
				csr_ack = 1;
				csr_rdval = csr_custom_ro_value;
			end
			default:
				;
		endcase
		csr_next = csr_rdval;
		case (csr_mode)
			2'b01: csr_next = csr_rsval;
			2'b10: csr_next = csr_next | csr_rsval;
			2'b11: csr_next = csr_next & ~csr_rsval;
		endcase
		csr_mstatus_wdata = (csr_mstatus_sel ? csr_next : csr_mstatus_value);
		csr_mstatus_next = csr_mstatus_wdata;
		csr_misa_wdata = (csr_misa_sel ? csr_next : csr_misa_value);
		csr_misa_next = csr_misa_wdata;
		csr_mie_wdata = (csr_mie_sel ? csr_next : csr_mie_value);
		csr_mie_next = csr_mie_wdata;
		csr_mtvec_wdata = (csr_mtvec_sel ? csr_next : csr_mtvec_value);
		csr_mtvec_next = csr_mtvec_wdata;
		csr_mstatush_wdata = (csr_mstatush_sel ? csr_next : csr_mstatush_value);
		csr_mstatush_next = csr_mstatush_wdata;
		csr_mscratch_wdata = (csr_mscratch_sel ? csr_next : csr_mscratch_value);
		csr_mscratch_next = csr_mscratch_wdata;
		csr_mepc_wdata = (csr_mepc_sel ? csr_next : csr_mepc_value);
		csr_mepc_next = csr_mepc_wdata;
		csr_mcause_wdata = (csr_mcause_sel ? csr_next : csr_mcause_value);
		csr_mcause_next = csr_mcause_wdata;
		csr_mtval_wdata = (csr_mtval_sel ? csr_next : csr_mtval_value);
		csr_mtval_next = csr_mtval_wdata;
		csr_mip_wdata = (csr_mip_sel ? csr_next : csr_mip_value);
		csr_mip_next = csr_mip_wdata;
		for (hpm_counter_idx = 0; hpm_counter_idx < 32; hpm_counter_idx = hpm_counter_idx + 1)
			csr_hpm_counter_wdata[hpm_counter_idx * 32+:32] = (csr_hpm_counter_sel[hpm_counter_idx] ? csr_next : csr_hpm_counter_value[hpm_counter_idx * 32+:32]);
		csr_hpm_counter_next = csr_hpm_counter_wdata;
		for (hpm_counterh_idx = 0; hpm_counterh_idx < 32; hpm_counterh_idx = hpm_counterh_idx + 1)
			csr_hpm_counterh_wdata[hpm_counterh_idx * 32+:32] = (csr_hpm_counterh_sel[hpm_counterh_idx] ? csr_next : csr_hpm_counterh_value[hpm_counterh_idx * 32+:32]);
		csr_hpm_counterh_next = csr_hpm_counterh_wdata;
		for (hpm_event_idx = 0; hpm_event_idx < 32; hpm_event_idx = hpm_event_idx + 1)
			csr_hpm_event_wdata[hpm_event_idx * 32+:32] = (csr_hpm_event_sel[hpm_event_idx] ? csr_next : csr_hpm_event_value[hpm_event_idx * 32+:32]);
		csr_hpm_event_next = csr_hpm_event_wdata;
		csr_custom_wdata = (csr_custom_sel ? csr_next : csr_custom_value);
		csr_custom_next = csr_custom_wdata;
		for (hpm_idx = 0; hpm_idx < 32; hpm_idx = hpm_idx + 1)
			begin
				case (hpm_idx)
					0: hpm_event = 32'h00000001;
					2: hpm_event = 32'h00000002;
					default: hpm_event = csr_hpm_event_next[hpm_idx * 32+:32];
				endcase
				case (hpm_event)
					32'h00000001: hpm_increment = 1;
					32'h00000002: hpm_increment = (running ? 1 : 0);
					32'h00000003: hpm_increment = (mem_wr_enable_q ? 1 : 0);
					default: begin
						csr_hpm_event_next[hpm_idx * 32+:32] = 0;
						hpm_increment = 0;
					end
				endcase
				{csr_hpm_counterh_next[hpm_idx * 32+:32], csr_hpm_counter_next[hpm_idx * 32+:32]} = {csr_hpm_counterh_next[hpm_idx * 32+:32], csr_hpm_counter_next[hpm_idx * 32+:32]} + hpm_increment;
			end
		csr_mstatus_next[31] = 'b0;
		csr_mstatus_next[30:23] = 'b0;
		csr_mstatus_next[22] = 'b0;
		csr_mstatus_next[21] = 'b0;
		csr_mstatus_next[20] = 'b0;
		csr_mstatus_next[19] = 'b0;
		csr_mstatus_next[18] = 'b0;
		csr_mstatus_next[17] = 'b0;
		csr_mstatus_next[16:15] = 'b0;
		csr_mstatus_next[14:13] = 'b0;
		csr_mstatus_next[12:11] = 2'b11;
		csr_mstatus_next[10:9] = 'b0;
		csr_mstatus_next[8] = 'b0;
		csr_mstatus_next[6] = 'b0;
		csr_mstatus_next[5] = 'b0;
		csr_mstatus_next[4] = 'b0;
		csr_mstatus_next[2] = 'b0;
		csr_mstatus_next[1] = 'b0;
		csr_mstatus_next[0] = 'b0;
		csr_mstatush_next[31:6] = 'b0;
		csr_mstatush_next[5] = 1'b0;
		csr_mstatush_next[4] = 'b0;
		csr_mstatush_next[3:0] = 'b0;
		csr_misa_next[31:20] = 'b0;
		csr_misa_next[29:26] = 'b0;
		csr_misa_next[25:0] = 'b0;
		csr_mie_next[15:12] = 'b0;
		csr_mie_next[10] = 'b0;
		csr_mie_next[9] = 'b0;
		csr_mie_next[8] = 'b0;
		csr_mie_next[6] = 'b0;
		csr_mie_next[5] = 'b0;
		csr_mie_next[4] = 'b0;
		csr_mie_next[2] = 'b0;
		csr_mie_next[1] = 'b0;
		csr_mie_next[0] = 'b0;
		csr_mip_next = irq & IRQ_MASK;
		csr_mtvec_next[1] = 'b0;
		csr_mcause_next[30:5] = 'b0;
		csr_mepc_next[1:0] = 'b0;
		case (insn_opcode)
			OPCODE_LUI: begin
				next_wr = 1;
				next_rd = insn[31:12] << 12;
			end
			OPCODE_AUIPC: begin
				next_wr = 1;
				next_rd = (insn[31:12] << 12) + pc;
			end
			OPCODE_JAL: begin
				next_wr = 1;
				next_rd = npc;
				npc = pc + imm_j_sext;
				if (npc & 32'b00000000000000000000000000000011) begin
					illinsn = 1;
					npc = npc & ~32'b00000000000000000000000000000011;
				end
			end
			OPCODE_JALR: begin
				case (insn_funct3)
					3'b000: begin
						next_wr = 1;
						next_rd = npc;
						npc = (rs1_value + imm_i_sext) & ~32'b00000000000000000000000000000001;
					end
					default: illinsn = 1;
				endcase
				if (npc & 32'b00000000000000000000000000000011) begin
					illinsn = 1;
					npc = npc & ~32'b00000000000000000000000000000011;
				end
			end
			OPCODE_BRANCH: begin
				case (insn_funct3)
					3'b000:
						if (rs1_value == rs2_value)
							npc = pc + imm_b_sext;
					3'b001:
						if (rs1_value != rs2_value)
							npc = pc + imm_b_sext;
					3'b100:
						if ($signed(rs1_value) < $signed(rs2_value))
							npc = pc + imm_b_sext;
					3'b101:
						if ($signed(rs1_value) >= $signed(rs2_value))
							npc = pc + imm_b_sext;
					3'b110:
						if (rs1_value < rs2_value)
							npc = pc + imm_b_sext;
					3'b111:
						if (rs1_value >= rs2_value)
							npc = pc + imm_b_sext;
					default: illinsn = 1;
				endcase
				if (npc & 32'b00000000000000000000000000000011) begin
					illinsn = 1;
					npc = npc & ~32'b00000000000000000000000000000011;
				end
			end
			OPCODE_LOAD: begin
				mem_rd_addr = rs1_value + imm_i_sext;
				casez ({insn_funct3, mem_rd_addr[1:0]})
					5'b000zz, 5'b001z0, 5'b01000, 5'b100zz, 5'b101z0: begin
						mem_rd_enable = 1;
						mem_rd_reg = insn_rd;
						mem_rd_func = {mem_rd_addr[1:0], insn_funct3};
						mem_rd_addr = {mem_rd_addr[31:2], 2'b00};
					end
					default: illinsn = 1;
				endcase
			end
			OPCODE_STORE: begin
				mem_wr_addr = rs1_value + imm_s_sext;
				casez ({insn_funct3, mem_wr_addr[1:0]})
					5'b000zz, 5'b001z0, 5'b01000: begin
						mem_wr_enable = 1;
						mem_wr_data = rs2_value;
						mem_wr_strb = 4'b1111;
						case (insn_funct3)
							3'b000: mem_wr_strb = 4'b0001;
							3'b001: mem_wr_strb = 4'b0011;
							3'b010: mem_wr_strb = 4'b1111;
						endcase
						mem_wr_data = mem_wr_data << (8 * mem_wr_addr[1:0]);
						mem_wr_strb = mem_wr_strb << mem_wr_addr[1:0];
						mem_wr_addr = {mem_wr_addr[31:2], 2'b00};
					end
					default: illinsn = 1;
				endcase
			end
			OPCODE_OP_IMM:
				casez ({insn_funct7, insn_funct3})
					10'bzzzzzzz000: begin
						next_wr = 1;
						next_rd = rs1_value + imm_i_sext;
					end
					10'bzzzzzzz010: begin
						next_wr = 1;
						next_rd = $signed(rs1_value) < $signed(imm_i_sext);
					end
					10'bzzzzzzz011: begin
						next_wr = 1;
						next_rd = rs1_value < imm_i_sext;
					end
					10'bzzzzzzz100: begin
						next_wr = 1;
						next_rd = rs1_value ^ imm_i_sext;
					end
					10'bzzzzzzz110: begin
						next_wr = 1;
						next_rd = rs1_value | imm_i_sext;
					end
					10'bzzzzzzz111: begin
						next_wr = 1;
						next_rd = rs1_value & imm_i_sext;
					end
					10'b0000000001: begin
						next_wr = 1;
						next_rd = rs1_value << insn[24:20];
					end
					10'b0000000101: begin
						next_wr = 1;
						next_rd = rs1_value >> insn[24:20];
					end
					10'b0100000101: begin
						next_wr = 1;
						next_rd = $signed(rs1_value) >>> insn[24:20];
					end
					10'b0110000001:
						casez (insn[24:20])
							5'b00000: begin
								next_wr = 1;
								next_rd = 0;
								begin : sv2v_autoblock_1
									reg signed [31:0] i;
									for (i = 0; i < 32; i = i + 1)
										next_rd = (rs1_value[i] ? 0 : next_rd + 1);
								end
							end
							5'b00001: begin
								next_wr = 1;
								next_rd = 0;
								begin : sv2v_autoblock_2
									reg signed [31:0] i;
									for (i = 32; i > 0; i = i - 1)
										next_rd = (rs1_value[i - 1] ? 0 : next_rd + 1);
								end
							end
							5'b00010: begin
								next_wr = 1;
								next_rd = 0;
								begin : sv2v_autoblock_3
									reg signed [31:0] i;
									for (i = 0; i < 32; i = i + 1)
										next_rd = next_rd + rs1_value[i];
								end
							end
							5'b00100: begin
								next_wr = 1;
								next_rd = $signed(rs1_value[7:0]);
							end
							5'b00101: begin
								next_wr = 1;
								next_rd = $signed(rs1_value[15:0]);
							end
							default: illinsn = 1;
						endcase
					10'b0110000101: begin
						next_wr = 1;
						next_rd = (rs1_value >> insn[24:20]) | (rs1_value << (32 - insn[24:20]));
					end
					10'b0010100101: begin
						next_wr = insn[24:20] == 5'b00111;
						illinsn = !next_wr;
						next_rd = 0;
						begin : sv2v_autoblock_4
							reg signed [31:0] i;
							for (i = 0; i < 4; i = i + 1)
								next_rd[i * 8+:8] = {8 {|rs1_value[i * 8+:8]}};
						end
					end
					10'b0110100101:
						casez (insn[24:20])
							5'b11000: begin
								next_wr = 1;
								next_rd = 0;
								begin : sv2v_autoblock_5
									reg signed [31:0] i;
									for (i = 0; i < 4; i = i + 1)
										next_rd[i * 8+:8] = rs1_value[((4 - i) * 8) - 1-:8];
								end
							end
							5'b00111: begin
								next_wr = 1;
								next_rd = 0;
								begin : sv2v_autoblock_6
									reg signed [31:0] i;
									for (i = 0; i < 4; i = i + 1)
										begin : sv2v_autoblock_7
											reg signed [31:0] j;
											for (j = 0; j < 8; j = j + 1)
												next_rd[(i * 8) + j] = rs1_value[((i * 8) + 7) - j];
										end
								end
							end
							default: illinsn = 1;
						endcase
					10'b0000100001: begin
						next_wr = insn[24:20] == 5'b01111;
						illinsn = !next_wr;
						next_rd = 0;
						begin : sv2v_autoblock_8
							reg signed [31:0] i;
							for (i = 0; i < 16; i = i + 1)
								begin
									next_rd[2 * i] = rs1_value[i];
									next_rd[(2 * i) + 1] = rs1_value[i + 16];
								end
						end
					end
					10'b0000100101: begin
						next_wr = insn[24:20] == 5'b01111;
						illinsn = !next_wr;
						next_rd = 0;
						begin : sv2v_autoblock_9
							reg signed [31:0] i;
							for (i = 0; i < 16; i = i + 1)
								begin
									next_rd[i] = rs1_value[2 * i];
									next_rd[i + 16] = rs1_value[(2 * i) + 1];
								end
						end
					end
					10'b0100100001: begin
						next_wr = 1;
						next_rd = rs1_value & ~(1 << insn[24:20]);
					end
					10'b0100100101: begin
						next_wr = 1;
						next_rd = (rs1_value >> insn[24:20]) & 1;
					end
					10'b0110100001: begin
						next_wr = 1;
						next_rd = rs1_value ^ (1 << insn[24:20]);
					end
					10'b0010100001: begin
						next_wr = 1;
						next_rd = rs1_value | (1 << insn[24:20]);
					end
					default: illinsn = 1;
				endcase
			OPCODE_OP:
				case ({insn_funct7, insn_funct3})
					10'b0000000000: begin
						next_wr = 1;
						next_rd = rs1_value + rs2_value;
					end
					10'b0100000000: begin
						next_wr = 1;
						next_rd = rs1_value - rs2_value;
					end
					10'b0000000001: begin
						next_wr = 1;
						next_rd = rs1_value << rs2_value[4:0];
					end
					10'b0000000010: begin
						next_wr = 1;
						next_rd = $signed(rs1_value) < $signed(rs2_value);
					end
					10'b0000000011: begin
						next_wr = 1;
						next_rd = rs1_value < rs2_value;
					end
					10'b0000000100: begin
						next_wr = 1;
						next_rd = rs1_value ^ rs2_value;
					end
					10'b0000000101: begin
						next_wr = 1;
						next_rd = rs1_value >> rs2_value[4:0];
					end
					10'b0100000101: begin
						next_wr = 1;
						next_rd = $signed(rs1_value) >>> rs2_value[4:0];
					end
					10'b0000000110: begin
						next_wr = 1;
						next_rd = rs1_value | rs2_value;
					end
					10'b0000000111: begin
						next_wr = 1;
						next_rd = rs1_value & rs2_value;
					end
					10'b0010000010: begin
						next_wr = 1;
						next_rd = rs2_value + {rs1_value[30:0], 1'b0};
					end
					10'b0010000100: begin
						next_wr = 1;
						next_rd = rs2_value + {rs1_value[29:0], 2'b00};
					end
					10'b0010000110: begin
						next_wr = 1;
						next_rd = rs2_value + {rs1_value[28:0], 3'b000};
					end
					10'b0100000111: begin
						next_wr = 1;
						next_rd = rs1_value & ~rs2_value;
					end
					10'b0100000110: begin
						next_wr = 1;
						next_rd = rs1_value | ~rs2_value;
					end
					10'b0100000100: begin
						next_wr = 1;
						next_rd = ~(rs1_value ^ rs2_value);
					end
					10'b0000101110: begin
						next_wr = 1;
						next_rd = ($signed(rs1_value) < $signed(rs2_value) ? rs2_value : rs1_value);
					end
					10'b0000101111: begin
						next_wr = 1;
						next_rd = (rs1_value < rs2_value ? rs2_value : rs1_value);
					end
					10'b0000101100: begin
						next_wr = 1;
						next_rd = ($signed(rs1_value) < $signed(rs2_value) ? rs1_value : rs2_value);
					end
					10'b0000101101: begin
						next_wr = 1;
						next_rd = (rs1_value < rs2_value ? rs1_value : rs2_value);
					end
					10'b0110000001: begin
						next_wr = 1;
						next_rd = (rs1_value << rs2_value[4:0]) | (rs1_value >> (32 - rs2_value[4:0]));
					end
					10'b0110000101: begin
						next_wr = 1;
						next_rd = (rs1_value >> rs2_value[4:0]) | (rs1_value << (32 - rs2_value[4:0]));
					end
					10'b0000100100: begin
						next_wr = 1;
						next_rd = {rs2_value[15:0], rs1_value[15:0]};
					end
					10'b0000100111: begin
						next_wr = 1;
						next_rd = {16'b0000000000000000, rs2_value[7:0], rs1_value[7:0]};
					end
					10'b0000101001: begin
						next_wr = 1;
						next_rd = 0;
						begin : sv2v_autoblock_10
							reg signed [31:0] i;
							for (i = 0; i < 32; i = i + 1)
								next_rd = (rs2_value[i] ? next_rd ^ (rs1_value << i) : next_rd);
						end
					end
					10'b0000101011: begin
						next_wr = 1;
						next_rd = 0;
						begin : sv2v_autoblock_11
							reg signed [31:0] i;
							for (i = 1; i < 33; i = i + 1)
								next_rd = ((rs2_value >> i) & 32'b00000000000000000000000000000001 ? next_rd ^ (rs1_value >> (32 - i)) : next_rd);
						end
					end
					10'b0000101010: begin
						next_wr = 1;
						next_rd = 0;
						begin : sv2v_autoblock_12
							reg signed [31:0] i;
							for (i = 0; i < 32; i = i + 1)
								next_rd = (rs2_value[i] ? next_rd ^ (rs1_value >> ((32 - i) - 1)) : next_rd);
						end
					end
					10'b0100100001: begin
						next_wr = 1;
						next_rd = rs1_value & ~(1 << rs2_value[4:0]);
					end
					10'b0100100101: begin
						next_wr = 1;
						next_rd = (rs1_value >> rs2_value[4:0]) & 1;
					end
					10'b0110100001: begin
						next_wr = 1;
						next_rd = rs1_value ^ (1 << rs2_value[4:0]);
					end
					10'b0010100001: begin
						next_wr = 1;
						next_rd = rs1_value | (1 << rs2_value[4:0]);
					end
					10'b0010100010: begin
						next_wr = 1;
						next_rd = 0;
						begin : sv2v_autoblock_13
							reg signed [31:0] i;
							for (i = 0; i < 8; i = i + 1)
								next_rd[i * 4+:4] = (rs1_value >> rs2_value[i * 4+:4]) & 4'hf;
						end
					end
					10'b0010100100: begin
						next_wr = 1;
						next_rd = 0;
						begin : sv2v_autoblock_14
							reg signed [31:0] i;
							for (i = 0; i < 4; i = i + 1)
								next_rd[i * 8+:8] = (rs1_value >> rs2_value[i * 8+:8]) & 8'hff;
						end
					end
					default: illinsn = 1;
				endcase
			OPCODE_SYSTEM:
				case (insn_funct3)
					3'b000:
						case ({insn_funct7, insn_rs2})
							12'b000000000000: begin
								csr_mepc_next = {pc[31:2], 2'b00};
								npc = csr_mtvec_value & ~3;
								csr_mcause_next = MCAUSE_ECALL_M_MODE;
								csr_mstatus_next[7] = csr_mstatus_value[3];
								csr_mstatus_next[3] = 0;
							end
							12'b000000000001: begin
								csr_mepc_next = {pc[31:2], 2'b00};
								npc = csr_mtvec_value & ~3;
								csr_mcause_next = MCAUSE_BREAKPOINT;
								csr_mstatus_next[7] = csr_mstatus_value[3];
								csr_mstatus_next[3] = 0;
							end
							12'b001100000010: begin
								npc = csr_mepc_value;
								csr_mcause_next = 'b0;
								csr_mstatus_next[3] = csr_mstatus_value[7];
							end
							12'b000100000101:
								;
							default: illinsn = 1;
						endcase
					default:
						if (csr_ack) begin
							next_wr = 1;
							next_rd = csr_rdval;
						end
						else
							illinsn = 1;
				endcase
			default: illinsn = 1;
		endcase
		if (reset || reset_q) begin
			npc = RESET_ADDR;
			csr_mstatus_next[3] = 0;
		end
		else if (stall)
			npc = pc;
		else if (mem_rd_enable_q) begin
			npc = pc;
			cycle_late_wr = 1;
			wr_rd = mem_rd_reg_q;
			next_rd = mem_rdata;
		end
		else if (irq_num != 0) begin
			csr_mepc_next = {pc[31:2], 2'b00};
			csr_mcause_next = 33'sd2147483648 | irq_num;
			if (csr_mtvec_value & 1)
				npc = (csr_mtvec_value & ~3) + (irq_num << 2);
			else
				npc = csr_mtvec_value & ~3;
			csr_mstatus_next[7] = 1;
			csr_mstatus_next[3] = 0;
			cycle_intr = 1;
		end
		else if (imem_fault || illinsn) begin
			cycle_trap = 1;
			csr_mepc_next[31:2] = pc[31:2];
			npc = csr_mtvec_value & ~3;
			csr_mcause_next = (imem_fault ? MCAUSE_INSN_ACCESS_FAULT : MCAUSE_INVALID_INSTRUCTION);
			csr_mcause_wdata = csr_mcause_next;
			csr_mstatus_next[7] = csr_mstatus_value[3];
			csr_mstatus_next[3] = 0;
		end
		else
			cycle_insn = 1;
		if (!cycle_insn) begin
			next_wr = cycle_late_wr && mem_rd_enable_q;
			mem_rd_enable = 0;
			mem_wr_enable = 0;
		end
	end
	always @(*) begin
		mem_rdata = dmem_rdata >> (8 * mem_rd_func_q[4:3]);
		case (mem_rd_func_q[2:0])
			3'b000: mem_rdata = $signed(mem_rdata[7:0]);
			3'b001: mem_rdata = $signed(mem_rdata[15:0]);
			3'b100: mem_rdata = mem_rdata[7:0];
			3'b101: mem_rdata = mem_rdata[15:0];
		endcase
	end
	always @(posedge clock) begin
		reset_q <= reset || (reset_q && stall);
		pc <= npc;
		if (next_wr)
			regfile[wr_rd] <= next_rd;
		if (reset || reset_q)
			pc <= RESET_ADDR - (reset ? 4 : 0);
	end
endmodule