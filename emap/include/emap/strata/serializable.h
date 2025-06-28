#ifndef SERIALIZABLE_H
#define SERIALIZABLE_H


namespace emap::strata {

template <typename S>
class Serializable {
public:
    virtual ~Serializable() = default;
    virtual S serialize() const = 0;
};

}


#endif