#include <cstddef>

#include "group_wires_v2.h"


namespace emapcc {

std::pair<std::vector<std::vector<int>>, std::vector<std::vector<int>>> group_wires_v2(std::vector<std::set<int>> bundles) {
    // returns the new bundles and groups
    std::vector<std::vector<int>> new_bundles(bundles.size());
    std::vector<std::vector<int>> groups;

    // preprocess
    std::map<int, std::set<std::size_t>> wire_to_bundles;
    for (std::size_t i = 0; i < bundles.size(); ++i) {
        const auto& bundle = bundles[i];
        for (auto wire : bundle) {
            auto itr = wire_to_bundles.find(wire);
            if (itr == wire_to_bundles.end()) {
                wire_to_bundles.insert({wire, {i}});
            }
            else {
                itr->second.insert(i);
            }
        }
    }

    // for each wire
    auto itr = wire_to_bundles.begin();
    while (itr != wire_to_bundles.end()) {
        // build the group candidate by intersecting bundles containing this wire
        const auto& [wire, hitting_bundles] = *itr;
        auto hitting_itr = hitting_bundles.begin();
        if (hitting_itr == hitting_bundles.end()) { // no bundles hit this wire
            wire_to_bundles.erase(itr);
            continue;
        }
        auto group_candidate = std::set<int>(bundles[*hitting_itr]);
        ++hitting_itr;
        while (hitting_itr != hitting_bundles.end()) {
            const auto& bundle = bundles[*hitting_itr];
            std::set<int> new_group_candidate;
            for (auto w : group_candidate) {
                if (bundle.find(w) != bundle.end()) {
                    new_group_candidate.insert(w);
                }
            }
            group_candidate = std::move(new_group_candidate);
            ++hitting_itr;
        }

        // check all wires in the group, if one exists in other bundles, remove it from group
        std::set<int> group;
        for (auto wire : group_candidate) {
            auto other_itr = wire_to_bundles.find(wire);
            bool valid = true;
            if (other_itr != wire_to_bundles.end()) {
                for (auto other_bundle : other_itr->second) {
                    if (hitting_bundles.find(other_bundle) == hitting_bundles.end()) {  // this wires is in other bundles
                        valid = false;
                        break;
                    }
                }
            }
            if (valid) {
                group.insert(wire);
            }
        }
#ifdef DEBUG
#include <iostream>
        std::cout << "Group for wire " << wire << ": ";
        for (auto w : group_candidate) {
            std::cout << w << " ";
        }
        std::cout << "\n";
#endif

        // update wire_to_bundles, bundles and new_bundles
        int group_index = groups.size();
        for (auto bundle : hitting_bundles) {
            new_bundles[bundle].push_back(group_index);
        }
        for (auto wire : group) {
            for (auto bundle : wire_to_bundles[wire]) {
                bundles[bundle].erase(wire);
            }
            wire_to_bundles.erase(wire);
        }
        groups.push_back(std::vector<int>(group.begin(), group.end()));
        itr = wire_to_bundles.begin(); // reset iterator to the beginning after modifying wire_to_bundles
    }

    return {new_bundles, groups};
}

}