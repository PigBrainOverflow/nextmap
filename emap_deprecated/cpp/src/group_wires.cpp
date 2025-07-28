#include <memory>

#include "group_wires.h"


namespace emapcc {

std::pair<std::vector<std::vector<int>>, std::vector<std::vector<int>>> group_wires(std::vector<std::set<int>> bundles) {
    // returns the new bundles and groups

    std::set<int> all_wires;
    for (const auto& bundle : bundles) {
        all_wires.insert(bundle.begin(), bundle.end());
    }

    std::vector<std::vector<int>> groups;
    std::vector<std::vector<int>> new_bundles(bundles.size(), std::vector<int>());

    for (auto wire : all_wires) {
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
        std::vector<int> bundles_to_update;
        for (int i = 0; i < bundles.size(); ++i) {
            const auto& bundle = bundles[i];
            if (bundle.find(wire) == bundle.end()) {    // wire not in this bundle
                // group_candidate = group_candidate - bundle
                for (auto w : bundle) {
                    group_candidate->erase(w);
                }
            }
            else {  // wire is in this bundle
                // group_candidate = group_candidate & bundle
                std::unique_ptr<std::set<int>> new_group_candidate = std::make_unique<std::set<int>>();
                for (auto w : *group_candidate) {
                    if (bundle.find(w) != bundle.end()) {
                        new_group_candidate->insert(w);
                    }
                }
                group_candidate = std::move(new_group_candidate);
                bundles_to_update.push_back(i);
            }
        }

        // add to groups
        auto group_index = groups.size();
        groups.push_back(std::vector<int>(group_candidate->begin(), group_candidate->end()));
        // update bundles and new_bundles
        for (auto i : bundles_to_update) {
            auto& bundle = bundles[i];
            for (auto w : *group_candidate) {
                bundle.erase(w);
            }
            auto& new_bundle = new_bundles[i];
            new_bundle.push_back(group_index);
        }

#ifdef DEBUG
#include <iostream>
        std::cout << "Group for wire " << wire << ": ";
        for (auto w : *group_candidate) {
            std::cout << w << " ";
        }
        std::cout << "\n";
#endif
    }

    return {new_bundles, groups};
}

}