#include <algorithm>
#include <cstddef>

#include "prune_cells.h"


namespace emapcc {

std::set<int> prune_cells(const std::vector<std::tuple<float, std::vector<int>, std::vector<int>>>& cells) {
    // cells is a vector of tuples (cost, inputs, outputs)
    std::set<int> removed_indices;

    // build a trie
    Trie<std::vector<int>, std::size_t> trie;
    for (std::size_t i = 0; i < cells.size(); ++i) {
        trie.insert(std::get<1>(cells[i]), i);
    }

    for (std::size_t i = 0; i < cells.size(); ++i) {
        const auto& [cost, inputs, outputs] = cells[i];
        // find all subsets of inputs
        auto candidates = trie.subseq_of(inputs);
        bool is_removable = false;
        for (auto candidate : candidates) {
            if (candidate == i) {
                continue; // skip self
            }
            const auto& [other_cost, _, other_outputs] = cells[candidate];
            if (other_cost <= cost && std::includes(
                other_outputs.begin(), other_outputs.end(),
                outputs.begin(), outputs.end()
            )) {
                // if the other cell is cheaper and has all outputs
                is_removable = true;
                break;
            }
        }
        if (is_removable) {
#ifdef DEBUG
#include <iostream>
            std::cout << "Removing cell " << i << " with cost " << cost
                      << " and inputs " << inputs.size() << " outputs " << outputs.size() << std::endl;
#endif
            removed_indices.insert(i);
            trie.remove(inputs, i);
        }
    }
    return removed_indices;
}

}