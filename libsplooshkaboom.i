
%include <stdint.i>
%include <std_string.i>
%include <std_vector.i>

%module libsplooshkaboom %{
    #include "libsplooshkaboom.h"
%}

%include "libsplooshkaboom.h"

namespace std {
    %template(vectori) vector<int>;
    %template(vectord) vector<double>;
}

