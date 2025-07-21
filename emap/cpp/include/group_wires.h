#ifndef GROUP_WIRES_H
#define GROUP_WIRES_H

#include <utility>
#include <vector>
#include <set>
#include <memory>


namespace emapcc {

std::pair<std::vector<std::vector<int>>, std::vector<std::vector<int>>> group_wires(std::vector<std::set<int>> bundles) {
    // returns the new bundles and groups

    std::set<int> all_wires;
    for (const auto& bundle : bundles) {
        all_wires.insert(bundle.begin(), bundle.end());
    }

    for (int wire : all_wires) {
        std::unique_ptr<std::set<int>> group_candidate = nullptr;
        for (const auto& bundle : bundles) {
            if (bundle.find(wire) != bundle.end()) {
                group_candidate = std::make_unique<std::set<int>>(bundle);
                break;
            }
        }
        if (!group_candidate) {
            continue; // no group found for this wire
        }

        // shrink the group candidate
        for (const auto& bundle : bundles) {
            
        }
    }
}

}

#endif