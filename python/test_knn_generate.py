###############################################################################
### Program Variables                                                       ###
###############################################################################

run_gpu  = 1
run_cpu  = 1
use_loop = 1

###############################################################################
### Implementation                                                          ###
###############################################################################

import numpy as np

def knn_distances(points, k):
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=k+1, algorithm='brute').fit(points)
    distances, indices = nn.kneighbors(points)
    distances = distances[:, 1:]
    distances **= 2
    return distances

def create_prefix():
    print('#include <catch2/catch_test_macros.hpp>')
    print('#include <catch2/matchers/catch_matchers_floating_point.hpp>')
    print('#include <libsycl.hpp>')
    print()
    print('#include <knn.hpp>')
    print('#include <arguments.hpp>')
    print('#include <xyzset.hpp>')
    print()
    print('#define TEST_KNN_RUN_GPU {}'.format(run_gpu))
    print('#define TEST_KNN_RUN_CPU {}'.format(run_cpu))
    print('#define KNN_TEST_USE_LOOP {}'.format(use_loop))
    print()
    print('enum exectype { TYPE_GPU, TYPE_CPU };')
    print()
    print('namespace gpu {')
    print('template <typename Ti, typename Tf>')
    print('static std::pair<std::vector<Ti>, std::vector<Tf>>')
    print('get_knn(')
    print('  std::vector<std::array<Tf,3>>& inset,')
    print('  const struct votess::vtargs& args')
    print(') {')
    print('  ')
    print('  const auto args_knn = args.get_knn();')
    print('  const auto k = args_knn.k;')
    print('  const auto size = inset.size();')
    print()
    print('  auto')
    print('  [id, offset] = xyzset::sort<Ti,Tf>(inset, args.get_xyzset());')
    print('  {')
    print('    if (!xyzset::validate_xyzset<Tf>(inset)) {')
    print('      std::cout<<"oops1"<<std::endl;')
    print('    }')
    print('    if (!xyzset::validate_id<Ti>(id)) {')
    print('      std::cout<<"oops2"<<std::endl;')
    print('    }')
    print('    if (!xyzset::validate_offset<Ti>(offset)) {')
    print('      std::cout<<"oops3"<<std::endl;')
    print('    }')
    print('    auto gr = args.get_xyzset().grid_resolution;')
    print('    if (!xyzset::validate_sort<Ti,Tf>(inset, id, gr)) {')
    print('      std::cout<<"oops4"<<std::endl;')
    print('      std::abort();')
    print('    }')
    print('  }')
    print()
    print('  std::vector<Tf> xyzset(3 * size);')
    print('  for (size_t i = 0; i < size; i++) {')
    print('    xyzset[size * 0 + i] = inset[i][0];')
    print('    xyzset[size * 1 + i] = inset[i][1];')
    print('    xyzset[size * 2 + i] = inset[i][2];')
    print('  }')
    print()
    print('  sycl::queue queue;')
    print()
    print('  sycl::buffer<Ti, 1>')
    print('  bid(id.data(), sycl::range<1>(id.size()));')
    print()
    print('  sycl::buffer<Tf, 1>')
    print('  bxyzset(xyzset.data(), sycl::range<1>(xyzset.size()));')
    print()
    print('  sycl::buffer<Ti, 1>')
    print('  boffset(offset.data(), sycl::range<1>(offset.size()));')
    print()
    print('  sycl::buffer<Ti, 1> bhid(sycl::range<1>(size * k));')
    print('  sycl::buffer<Tf, 1> bhpq(sycl::range<1>(size * k));')
    print()
    print('  queue.submit([&](sycl::handler& cgh) {')
    print('    auto ahid = bhid.template')
    print('    get_access<sycl::access::mode::read_write>(cgh);')
    print('    cgh.fill(ahid, 0);')
    print('  });')
    print()
    print('  queue.submit([&](sycl::handler& cgh) {')
    print('    auto ahpq = bhpq.template')
    print('    get_access<sycl::access::mode::read_write>(cgh);')
    print('    cgh.fill(ahpq, 32.00f);')
    print('  });')
    print()
    print('  queue.submit([&](sycl::handler& cgh) {')
    print()
    print('    auto axyzset = bxyzset.template')
    print('    get_access<sycl::access::mode::read>(cgh);')
    print()
    print('    auto aid = bid.template')
    print('    get_access<sycl::access::mode::read>(cgh);')
    print()
    print('    auto aoffset = boffset.template')
    print('    get_access<sycl::access::mode::read>(cgh);')
    print()
    print('    auto ahid = bhid.template')
    print('    get_access<sycl::access::mode::read_write>(cgh);')
    print('    auto ahpq = bhpq.template')
    print('    get_access<sycl::access::mode::read_write>(cgh);')
    print()
    print('    auto aargs_knn = args_knn;')
    print('    cgh.parallel_for<class knn_sycl>(')
    print('      sycl::range<1>(xyzset.size() / 3),')
    print('      [=](sycl::id<1> idx) {')
    print('        knni::compute<Ti,Tf>(')
    print('          idx[0], idx[0],')
    print('          axyzset, size, aid, aoffset,')
    print('          axyzset, size,')
    print('          ahid, ahpq, size,')
    print('          aargs_knn')
    print('        );')
    print('      });')
    print()
    print('    queue.wait();')
    print()
    print('  });')
    print()
    print('  std::vector<Ti> vid(size * k);')
    print('  std::vector<Tf> vpq(size * k);')
    print('  auto ahid = bhid.get_host_access();')
    print('  auto ahpq = bhpq.get_host_access();')
    print()
    print('#if 1')
    print('  for (size_t i = 0; i < size; ++i) {')
    print('    for (size_t j = 0; j < k; ++j) {')
    print('      vid[i * k + j] = ahid[j * size + i];')
    print('      vpq[i * k + j] = ahpq[j * size + i];')
    print('    }')
    print('  }')
    print('#endif')
    print()
    print('  return {vid, vpq};')
    print()
    print('}')
    print()
    print('} // namespace gpu')
    print()
    print('namespace cpu {')
    print('template <typename Ti, typename Tf>')
    print('static std::pair<std::vector<Ti>, std::vector<Tf>>')
    print('get_knn(')
    print('  std::vector<std::array<Tf,3>>& inset,')
    print('  const struct votess::vtargs& args')
    print(') {')
    print()
    print('  auto [id, offset] = xyzset::sort<Ti,Tf>(inset, args.get_xyzset());')
    print('  {')
    print('    if (!xyzset::validate_xyzset<Tf>(inset)) {')
    print('      std::cout<<"oops1"<<std::endl;')
    print('    }')
    print('    if (!xyzset::validate_id<Ti>(id)) {')
    print('      std::cout<<"oops2"<<std::endl;')
    print('    }')
    print('    if (!xyzset::validate_offset<Ti>(offset)) {')
    print('      std::cout<<"oops3"<<std::endl;')
    print('    }')
    print('    auto gr = args.get_xyzset().grid_resolution;')
    print('    if (!xyzset::validate_sort<Ti,Tf>(inset, id, gr)) {')
    print('      std::cout<<"oops4"<<std::endl;')
    print('      std::abort();')
    print('    }')
    print('  }')
    print()
    print('  std::vector<Ti> vid(inset.size() * args.get_knn().k, 0);')
    print('  std::vector<Tf> vpq(inset.size() * args.get_knn().k, 32.00f);')
    print()
    print('  const auto args_knn = args.get_knn();')
    print('  for (size_t idx = 0; idx < inset.size(); ++idx) {')
    print('    knni::compute<Ti, Tf>(')
    print('      idx, idx,')
    print('      inset, inset.size(), id, offset,')
    print('      inset, inset.size(),')
    print('      vid, vpq,')
    print('      args_knn')
    print('    );')
    print('  }')
    print()
    print('  return {vid, vpq};')
    print('}')
    print('} // namespace cpu')
    print()
    print('template <typename Ti, typename Tf>')
    print('static void test_knn(')
    print('  std::vector<std::array<Tf, 3>>& xyzset,')
    print('  const std::vector<std::array<Tf, 3>>& kid,')
    print('  const std::vector<std::vector<Tf>>& kpq,')
    print('  const unsigned short int k_max,')
    print('  const unsigned short int gr_max,')
    print('  const Tf tol,')
    print('  enum exectype type')
    print(') {')
    print()
    print('#if KNN_TEST_USE_LOOP')
    print('  for (auto gr0 = 1; gr0 <= gr_max; gr0++) {')
    print('    const auto k0 = k_max;')
    print('    INFO("Looping with gr0 = " + std::to_string(gr0) + ')
    print('         ", k0 = " + std::to_string(k0));')
    print('#else')
    print('    const auto k0 = k_max;')
    print('    const auto gr0 = gr_max;')
    print('    INFO("Running without loop: k0 = " + std::to_string(k0) + ')
    print('         ", gr0 = " + std::to_string(gr0));')
    print('#endif')
    print()
    print('    std::string prefix = (type == TYPE_GPU) ? "[GPU] " : "[CPU] ";')
    print('    SECTION(prefix + "case : k0 = " + std::to_string(k0) + ')
    print('            ", gr = " + std::to_string(gr0)) {')
    print()
    print('      votess::vtargs args;')
    print('      args["k"] = k0;')
    print('      args["knn_grid_resolution"] = gr0;')
    print('      const auto [hid, hpq] = (type == TYPE_GPU) ? ')
    print('                              gpu::get_knn<Ti, Tf>(xyzset, args):')
    print('                              cpu::get_knn<Ti, Tf>(xyzset, args);')
    print()
    print('      for (size_t i = 0; i < xyzset.size(); i++) {')
    print('        const auto& point = xyzset[i];')
    print()
    print('        int index = -1;')
    print('        for (size_t j = 0; j < kid.size(); j++) {')
    print('          if (point == kid[j]) {')
    print('            index = j;')
    print('            break;')
    print('          }')
    print('        }')
    print()
    print('        REQUIRE(index != -1);')
    print('        INFO("Matched index: " + std::to_string(index));')
    print()
    print('        CAPTURE(i);')
    print('        CAPTURE(point);')
    print('        CAPTURE(kid[index]);')
    print()
    print('        std::vector<Tf> hpq_index;')
    print('        for (auto ki = 0; ki < k0; ki++) {')
    print('          hpq_index.emplace_back(hpq[k0 * i + ki]);')
    print('        }')
    print()
    print('        CAPTURE(kpq[index]);')
    print('        CAPTURE(hpq_index);')
    print()
    print('        for (size_t ki = 0; ki < k0; ki++) {')
    print('          CAPTURE(hpq[k0 * i + ki], kpq[index][ki]);')
    print()
    print('          REQUIRE_THAT(hpq[k0 * i + ki], ')
    print('                       Catch::Matchers::WithinRel(kpq[index][ki], tol));')
    print()
    print('        }')
    print()
    print('      }')
    print('    }')
    print()
    print('#if KNN_TEST_USE_LOOP')
    print('  }')
    print('#endif')
    print()
    print('}')

def create_test_case(tag, i, points, k_max, gr_max, tol=1e-9):

    import textwrap

    kpq = knn_distances(points, k_max)
    decimal_places = 12
 
    print(f'TEST_CASE("[float] knn regression {tag}: {i}", "[knn]") {{')
      
    print('\n  std::vector<std::array<float, 3>> xyzset = {')
    for point in points:
        print('    {{{:.{dec}f}f, {:.{dec}f}f, {:.{dec}f}f}},'
              .format(point[0], point[1], point[2], dec=decimal_places))
    print('  };')
 
    print('\n  std::vector<std::array<float, 3>> kid = xyzset;')
      
    print('\n  std::vector<std::vector<float>> kpq = {')
    for row in kpq:
        row_str = ', '.join(f'{dist:.{decimal_places}f}f' for dist in row)
        wrapped_row = textwrap.fill(row_str, width=79 - 6, 
                                    subsequent_indent=' ' * 8)
        print(f'    {{{wrapped_row}}},')
    print('  };')
 
    print(f'\n  const unsigned short int k_max = {k_max};')
    print(f'  const unsigned short int gr_max = {gr_max};')
    print(f'  const float tol = {tol};')
 
    print('  #if TEST_KNN_RUN_GPU')
    print('  test_knn<int, float>(xyzset, kid, kpq, k_max,')
    print('                       gr_max, tol, TYPE_GPU);')
    print('  #endif')
 
    print('  #if TEST_KNN_RUN_CPU')
    print('  test_knn<int, float>(xyzset, kid, kpq, k_max,')
    print('                       gr_max, tol, TYPE_CPU);')
    print('  #endif')
 
    print('}\n')

###############################################################################
### Test Cases                                                              ###
###############################################################################

def create_standard_xyzset():
    return np.array([
        [0.605223, 0.108484, 0.090937],
        [0.500792, 0.499641, 0.464576],
        [0.437936, 0.786332, 0.160392],
        [0.663354, 0.170894, 0.810284],
        [0.614869, 0.096867, 0.204147],
        [0.556911, 0.895342, 0.802266],
        [0.305748, 0.124146, 0.516249],
        [0.406888, 0.157835, 0.919622],
        [0.094412, 0.861991, 0.798644],
        [0.511958, 0.560537, 0.345479]
    ])

def create_random_xyzset(n_points=128):
    return np.random.rand(n_points, 3)

def create_clustered_xyzset(center, n_points=100, scale=0.1):
    return np.random.normal(loc=center, scale=scale, size=(n_points, 3))

def create_lattice_xyzset(grid_size=8):
    return np.array([[x, y, z] for x in np.linspace(0.1, 0.9, grid_size)
                                for y in np.linspace(0.1, 0.9, grid_size)
                                for z in np.linspace(0.1, 0.9, grid_size)])

def create_fibonacci_sphere_xyzset(n_points=128):
    golden_ratio = (1 + np.sqrt(5)) / 2
    indices = np.arange(0, n_points, dtype=float) + 0.5
    phi = 2 * np.pi * indices / golden_ratio
    theta = np.arccos(1 - 2*indices/n_points)
    
    # Spherical to Cartesian coordinates conversion
    x = np.cos(phi) * np.sin(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(theta)
    
    # Normalizing coordinates to fit within (0,1) exclusive
    min_val = min(x.min(), y.min(), z.min())
    max_val = max(x.max(), y.max(), z.max())
    x = (x - min_val) / (max_val - min_val)
    y = (y - min_val) / (max_val - min_val)
    z = (z - min_val) / (max_val - min_val)
    
    # Ensuring values are strictly within (0,1) exclusive
    epsilon = 1e-6
    x = np.clip(x, epsilon, 1 - epsilon)
    y = np.clip(y, epsilon, 1 - epsilon)
    z = np.clip(z, epsilon, 1 - epsilon)
    
    return np.column_stack((x, y, z))

def create_two_points_epsilon_xyzset(epsilon=1e-8):
    return np.array([
        [0.5, 0.5, 0.5],
        [0.5 + epsilon, 0.5, 0.5]
    ])

def create_degenerate_xyzset(N=128):
    point = np.array([[0.5, 0.5, 0.5]])
    return np.tile(point, (N, 1))

def create_sparse_xyzset(num_points=100, sparsity_level=0.95):
    data = np.random.rand(num_points, 3)
    mask = np.random.rand(num_points, 3) > sparsity_level
    sparse_data = data * mask
    return np.clip(sparse_data, 1e-6, 1 - 1e-6)

def create_noisy_xyzset(base_set, noise_level=0.1):
    noise = np.random.randn(*base_set.shape) * noise_level
    noisy_data = base_set + noise
    return np.clip(noisy_data, 1e-6, 1 - 1e-6)

def create_outliers_xyzset(base_set, outlier_factor=10):
    num_outliers = 5
    outliers = np.random.rand(num_outliers, 3) * outlier_factor
    outliers = np.clip(outliers, 1e-6, 1 - 1e-6)
    return np.vstack((base_set, outliers))

def create_imbalanced_class_xyzset(majority_class_size=200,
                                   minority_class_size=4):
    majority_class = np.random.rand(majority_class_size, 3)
    minority_class = (np.random.rand(minority_class_size, 3) * 0.1) + 0.9
    majority_class = np.clip(majority_class, 1e-10, 1 - 1e-10)
    minority_class = np.clip(minority_class, 1e-10, 1 - 1e-10)
    return np.vstack((majority_class, minority_class))

def create_collinear_xyzset(x_range=(0.01, 0.99),
                            y_value=0.5, z_value=0.5, n_points=128):

    return np.array([[x, y_value, z_value] 
                     for x in np.linspace(x_range[0], x_range[1], n_points)])

def create_concentric_xyzset(center=np.array([0.5, 0.5, 0.5]),
                             radius=0.1, n_points=100):

    angles = np.random.uniform(0, 2*np.pi, n_points)
    z = np.random.uniform(-1, 1, n_points)
    r = np.sqrt(1 - z**2)
    x = r * np.cos(angles)
    y = r * np.sin(angles)
    sphere_points = np.column_stack((x, y, z))
    scaled_points = sphere_points * radius
    return center + scaled_points


###############################################################################
### Main                                                                    ###
###############################################################################

def main():
    index = 0
    
    # standard
    xyzset = create_standard_xyzset()
    k = len(xyzset) - 1 
    gr = 24 
    tol = 1e-6
    create_test_case("standard", index, xyzset, k, gr, tol)
    index += 1
    
    # random tests
    for i in range(16):
        xyzset = create_random_xyzset()
        k = len(xyzset) - 1 
        gr = 1 
        tol = 1e-3
        create_test_case("random", index, xyzset, k, gr, tol)
        index += 1
    
    # clustered dataset
    cluster_center = np.array([0.5, 0.5, 0.5])
    xyzset = create_clustered_xyzset(cluster_center)
    k = len(xyzset) - 1
    gr = 23 
    tol = 1e-3
    create_test_case("clustered", index, xyzset, k, gr, tol)
    index += 1

    # lattice (between 0,1 exclusive)
    xyzset = create_lattice_xyzset()
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-3
    create_test_case("lattice", index, xyzset, k, gr, tol)
    index += 1

    # Fibonacci sphere
    for N in [8,24,64,128]:
        xyzset = create_fibonacci_sphere_xyzset(N)
        k = len(xyzset) - 1
        gr = 24
        tol = 1e-3
        create_test_case("fibonacci_sphere({})".format(N),
                         index, xyzset, k, gr, tol)
        index += 1

    # Two points separated by epsilon
    xyzset = create_two_points_epsilon_xyzset()
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-12
    create_test_case("two_points_epsilon", index, xyzset, k, gr, tol)
    index += 1

    # Degenerate cases
    xyzset = create_degenerate_xyzset()
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-3
    create_test_case("degenerate_cases", index, xyzset, k, gr, tol)
    index += 1

    # Sparse data
    xyzset = create_sparse_xyzset(num_points=100, sparsity_level=0.95)
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-3
    create_test_case("sparse_data", index, xyzset, k, gr, tol)
    index += 1

    # Noisy data
    base_set = create_lattice_xyzset()
    xyzset = create_noisy_xyzset(base_set, noise_level=0.1)
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-3
    create_test_case("noisy_data", index, xyzset, k, gr, tol)
    index += 1

    # Outliers
    base_set = create_standard_xyzset()
    xyzset = create_outliers_xyzset(base_set, outlier_factor=10)
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-3
    create_test_case("outliers", index, xyzset, k, gr, tol)
    index += 1

    # Imbalanced classes
    xyzset = create_imbalanced_class_xyzset(majority_class_size=200,
                                            minority_class_size=4)
    k = len(xyzset) - 1
    gr = 16 
    tol = 1e-3
    create_test_case("imbalanced_classes", index, xyzset, k, gr, tol)
    index += 1

    # Collinear points
    xyzset = create_collinear_xyzset()
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-3
    index += 1

    # Concentric points
    xyzset = create_concentric_xyzset()
    k = len(xyzset) - 1
    gr = 24
    tol = 1e-3
    create_test_case("concentric", index, xyzset, k, gr, tol)
    index += 1

    return 

if __name__ == "__main__":
    create_prefix()
    main()
