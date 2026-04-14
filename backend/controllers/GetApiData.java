import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;

public class GetApiData {
    public static void main(String[] args) throws IOException {
        int port = 2026;

        //Creates new HTTP Server
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        //Mapping url paths.
        server.createContext("/api/data", new HandleDataAPI());
        server.setExecutor(null);

        System.out.println("Starting Backend server: http://localhost:" + port + "/api/data");

        server.start();
    }

    //Nested class that handles http requests.
    private static class HandleDataAPI implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {

            //If the user request is an HTTP option.
            if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {

                addCorsResponse(exchange);
                exchange.sendResponseHeaders(204, -1);
                return;
            }

            //If user request is not Get.
            if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                addCorsResponse(exchange);
                exchange.sendResponseHeaders(405, -1);
                return;
            }

            //Gets combined_data.json
            Optional<Path> combinedDataPath = findCombinedDataPath();

            //If no data path exist. Then create JSON file with error message.
            if (combinedDataPath.isEmpty()) {
                addCorsResponse(exchange);
                String notFound = "{\"error\": \"combined_data.json is not found\"}";
                byte[] bytes = notFound.getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
                exchange.sendResponseHeaders(500, bytes.length);
                exchange.getResponseBody().write(bytes);
                exchange.close();
                return;
            }

            //Reading combined_data.json file.
            try {
                byte[] fileBytes = Files.readAllBytes(combinedDataPath.get());
                addCorsResponse(exchange);
                exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
                exchange.sendResponseHeaders(200, fileBytes.length);
                exchange.getResponseBody().write(fileBytes);

            } 

            //If reading fails.
            catch (IOException e) {
                addCorsResponse(exchange);
                String error = "{\"error\": \"Could not read combined_data.json: " + e.getMessage() + "\"}";
                byte[] bytes = error.getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
                exchange.sendResponseHeaders(500, bytes.length);
                exchange.getResponseBody().write(bytes);
            } 

            //Clean up file.
            finally {
                exchange.close();
            }
        }
    }

    //Gets combined_data.json file from possible locations.
    private static Optional<Path> findCombinedDataPath() {
        Path[] candidates = new Path[] {
            Path.of("output", "combined_data.json"),
            Path.of("backend", "output", "combined_data.json"),
            Path.of("..", "output", "combined_data.json"),
            Path.of("..", "..", "output", "combined_data.json")
        };

        for (Path path : candidates) {
            if (Files.exists(path)) {
                return Optional.of(path);
            }
        }
        return Optional.empty();
    }

    //Adds Cors response headers.
    private static void addCorsResponse(HttpExchange exchange) {
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "http://localhost:3000");
        exchange.getResponseHeaders().set("Access-Control-Allow-Methods", "GET, OPTIONS");
        exchange.getResponseHeaders().set("Access-Control-Allow-Headers", "Content-Type");
    }
}
