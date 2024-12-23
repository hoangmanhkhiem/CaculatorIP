from flask import Flask, request, render_template
import ipaddress

app = Flask(__name__)

def calculate_subnets(base_network_cidr, requirements):
    try:
        # Define the base network
        base_network = ipaddress.IPv4Network(base_network_cidr)
    except ValueError as e:
        return f"Invalid network input: {e}", {}

    # Sort requirements by number of hosts in descending order
    sorted_requirements = sorted(requirements.items(), key=lambda x: x[1], reverse=True)

    # Subnet calculations
    subnets = {}
    remaining_networks = [base_network]

    for name, hosts in sorted_requirements:
        # Calculate the smallest subnet mask that can accommodate the required hosts
        required_addresses = hosts + 2  # +2 for network and broadcast
        for i, network in enumerate(remaining_networks):
            if network.num_addresses >= required_addresses:
                new_prefix = 32 - (required_addresses - 1).bit_length()
                subnet = next(network.subnets(new_prefix=new_prefix))

                # Update remaining networks
                remaining_networks.pop(i)
                remaining_networks.extend(network.address_exclude(subnet))
                remaining_networks = sorted(remaining_networks, key=lambda x: x.prefixlen)

                # Store subnet details
                subnets[name] = {
                    "Network Address": f"{subnet.network_address}/{subnet.prefixlen}",
                    "Broadcast Address": subnet.broadcast_address,
                    "First Usable IP Address": list(subnet.hosts())[0],
                    "Last Usable IP Address": list(subnet.hosts())[-1],
                    "Number of Wasted IP": subnet.num_addresses - required_addresses,
                }
                break

    return None, subnets

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    base_network = request.form['base_network']
    requirements = {}

    for key, value in request.form.items():
        if key.startswith('req_') and value.strip():
            name = key[4:]  # Remove 'req_' prefix
            requirements[name] = int(value)

    # Sort requirements by number of hosts in descending order
    requirements = dict(sorted(requirements.items(), key=lambda x: x[1], reverse=True))

    error, results = calculate_subnets(base_network, requirements)
    if error:
        return render_template('error.html', error=error)

    if not results:
        return render_template('error.html', error="No subnets could be calculated. Please check your input.")

    return render_template('results.html', results=results)

if __name__ == "__main__":
    app.run(debug=True)
